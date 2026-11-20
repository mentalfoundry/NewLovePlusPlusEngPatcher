"""Date-info clock day mark: pkg 4138 dat_info_clo_txt_day 日 -> d (raw RGBA8 TEX)."""

from __future__ import annotations

import random
import struct
import zlib

import pytest
from conftest import TOOLS, load_module
from PIL import Image

dg = load_module("deploy_date_day_glyph_en", TOOLS / "deploy_date_day_glyph_en.py")
rebuild = load_module("rebuild_bake_img", TOOLS / "rebuild_bake_img.py")

NAME = dg.NAME


def texi(w: int = 8, h: int = 8, fmt: int = 10) -> bytes:
    meta = bytearray(82)
    struct.pack_into("<H", meta, 50, w)
    struct.pack_into("<H", meta, 54, h)
    meta[62] = fmt
    return bytes(meta)


def noise(n: int, seed: int) -> bytes:
    return random.Random(seed).randbytes(n)


def package(textures: list[tuple[str, bytes]], *, fmt: int = 10, w: int = 8) -> bytes:
    import fake_img as fi

    metas = [(f"{name}.texi", texi(w=w, fmt=fmt), b"TEXI", False) for name, _d in textures]
    texs = [(f"{name}.texi", data, b"TEX ", True) for name, data in textures]
    return fi.package([*metas, *texs])


def _patch(tmp_path, raw: bytes, master=None) -> bytes:
    path = tmp_path / f"p{zlib.crc32(raw):08x}"
    path.write_bytes(raw)
    return dg.patch_package(raw, path, master or dg.MASTER)


def _tex(tmp_path, raw: bytes, name: str) -> bytes:
    path = tmp_path / f"t{zlib.crc32(raw):08x}"
    path.write_bytes(raw)
    *_meta, cmp_len, cmp_off = dg.tex_slots(raw, path)[name]
    return zlib.decompress(raw[cmp_off : cmp_off + cmp_len])


def test_master_is_a_white_d_on_transparent():
    im = Image.open(dg.MASTER).convert("RGBA")
    assert im.size == dg.SIZE
    white = {(x, y) for y in range(8) for x in range(8) if im.getpixel((x, y)) == (255, 255, 255, 255)}
    # stem on the right, bowl on the left (rows 1-6, columns 2-6, like the digits)
    assert {(6, y) for y in range(1, 7)} <= white
    assert {(2, 4), (2, 5)} <= white and (2, 1) not in white
    assert im.getpixel((0, 0))[3] == 0


def test_encode_rgba8_tile_is_abgr_in_morton_order():
    im = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    im.putpixel((1, 0), (10, 20, 30, 40))  # Morton index 1
    im.putpixel((0, 1), (1, 2, 3, 4))  # Morton index 2
    out = dg.encode_rgba8_tile(im)
    assert len(out) == 256
    assert out[4:8] == bytes((40, 30, 20, 10))
    assert out[8:12] == bytes((4, 3, 2, 1))
    assert out[:4] == bytes(4)


def test_patch_package_replaces_only_the_day_tile(tmp_path):
    raw = package([("dat_info_clo_num_01", noise(256, 1)), (NAME, noise(256, 2))])
    new = _patch(tmp_path, raw)
    assert len(new) == len(raw)
    assert _tex(tmp_path, new, NAME) == dg.encode_rgba8_tile(Image.open(dg.MASTER))
    assert _tex(tmp_path, new, "dat_info_clo_num_01") == noise(256, 1)


@pytest.mark.parametrize(
    ("raw", "why"),
    [
        (package([("other", noise(256, 1))]), "missing"),
        (package([(NAME, noise(512, 1))], fmt=10, w=16), "unexpected TEX"),
        (package([(NAME, noise(128, 1))], fmt=9), "unexpected TEX"),
        (package([(NAME, bytes(256))]), "does not fit"),  # a blank tile's slot is a dozen bytes
    ],
)
def test_patch_package_refuses(tmp_path, raw, why):
    with pytest.raises(SystemExit, match=why):
        _patch(tmp_path, raw)


def test_patch_package_needs_an_8x8_master(tmp_path):
    big = tmp_path / "big.png"
    Image.new("RGBA", (16, 8)).save(big)
    with pytest.raises(SystemExit, match="expected"):
        _patch(tmp_path, package([(NAME, noise(256, 2))]), big)


def test_bake_runs_it_before_cesa():
    scripts = rebuild.DEPLOY_SCRIPTS
    assert scripts.index("deploy_date_day_glyph_en.py") < scripts.index("deploy_cesa_en.py")


def _env(tmp_path, monkeypatch, packages):
    import fake_img as fi

    tmp_path.mkdir(parents=True, exist_ok=True)
    fi.use_paths(monkeypatch, tmp_path, dg)
    monkeypatch.setattr(dg, "PKG", 7)
    vanilla = tmp_path / "vanilla.bin"
    vanilla.write_bytes(fi.img(packages, count=9))
    mod = tmp_path / "release" / "bake_img.bin"
    mod.parent.mkdir(parents=True, exist_ok=True)
    mod.write_bytes(vanilla.read_bytes())
    monkeypatch.setattr(dg, "MOD_IMG", mod)
    monkeypatch.setattr(dg, "OUT", tmp_path / "out")
    monkeypatch.setattr(dg, "_vanilla_src", lambda: vanilla)
    monkeypatch.setattr(dg, "_deploy_targets", lambda: [mod])
    return mod


def test_main_splices_the_package(tmp_path, monkeypatch):
    import fake_img as fi

    mod = _env(tmp_path, monkeypatch, {7: package([(NAME, noise(256, 2))])})
    assert dg.main() == 0
    got = fi.read_package(mod, 7)
    assert _tex(tmp_path, got, NAME) == dg.encode_rgba8_tile(Image.open(dg.MASTER))
    before = mod.read_bytes()
    assert dg.main() == 0  # starts from vanilla again
    assert mod.read_bytes() == before


def test_main_errors(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch, {7: package([(NAME, noise(256, 2))])})

    def boom(*_a):
        raise dg.PackError("grew")

    monkeypatch.setattr(dg, "splice_packages_into_img", boom)
    with pytest.raises(SystemExit, match="splice failed: grew"):
        dg.main()
    _env(tmp_path / "x", monkeypatch, {8: package([(NAME, noise(256, 2))])})
    with pytest.raises(SystemExit, match="pkg 7 missing"):
        dg.main()
    monkeypatch.setattr(dg, "MOD_IMG", tmp_path / "none.bin")
    with pytest.raises(SystemExit, match="missing"):
        dg.main()


@pytest.mark.local_data
def test_vanilla_package_takes_the_d_in_its_slot(tmp_path):
    from img import Image as ImgBin

    from nlpp_paths import find_vanilla_img

    vanilla = find_vanilla_img()
    if vanilla is None:
        pytest.skip("no vanilla img.bin")
    img = ImgBin(str(vanilla))
    img.parse(False)
    raw = img.entries[dg.PKG].fw.read()
    img.fh.close()
    new = _patch(tmp_path, raw)
    assert len(new) == len(raw)
    assert _tex(tmp_path, new, NAME) == dg.encode_rgba8_tile(Image.open(dg.MASTER))
    changed = [i for i in range(len(raw)) if raw[i] != new[i]]
    *_meta, cmp_len, cmp_off = dg.tex_slots(raw, tmp_path / f"p{zlib.crc32(raw):08x}")[NAME]
    assert cmp_off <= changed[0] and changed[-1] < cmp_off + cmp_len
