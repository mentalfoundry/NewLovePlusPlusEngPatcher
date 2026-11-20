#!/usr/bin/env python3
"""EN date-info clock day mark: 日 -> "d" in img.bin pkg **4138**.

pkg 4138 is the date HUD (gaze / TYPE / FEELING icons) plus a set of 8×8
``dat_info_clo_*`` clock tiles: digits, colon, and ``dat_info_clo_txt_day``
(日, as in "19日 23:45"). The month / weekday / AM-PM / weather tiles of the
same set are fully transparent, and no screen draws the clock: a probe with
red digits and a red D showed nothing on the home screen or through a whole
Call Out date (rig, 2026-11-19). The tile is replaced anyway so the package
carries no Japanese, giving "19d 23:45" if anything ever draws it.

  dat_info_clo_txt_day  8×8 RGBA8 (TEXI fmt 10), zlib slot 79

The master ``assets/images/date_info/dat_info_clo_txt_day.png``
(``work/render_date_day_glyph.py``) is a lowercase d in the digits' style:
white 1 px strokes, black drop shadow fitted to the digit tiles. It is
written as raw RGBA8 texels (transparent texels stay 0, as in vanilla) and
spliced into the tile's own zlib slot.

  python tools/deploy_date_day_glyph_en.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "nlpp-tools"))

from bclimutil import d2xy
from deploy_common import maybe_backup_img, resolve_img_paths
from deploy_minigame_textures_en import _deploy_targets, _vanilla_src, try_compress_to_slot
from deploy_photo_contest_en import tex_slots
from img import Image as ImgBin

from pack_images import PackError, splice_packages_into_img

MOD_IMG, _FALLBACK_VANILLA = resolve_img_paths()
MASTER = ROOT / "assets" / "images" / "date_info" / "dat_info_clo_txt_day.png"
OUT = ROOT / "out" / "date_day_glyph_en"
PKG = 4138
NAME = "dat_info_clo_txt_day"
SIZE = (8, 8)
FMT_RGBA8 = 10


def encode_rgba8_tile(im: Image.Image) -> bytes:
    """One 8×8 tile of PICA RGBA8 (bytes A, B, G, R in Morton order)."""
    px = im.convert("RGBA").load()
    out = bytearray()
    for k in range(64):
        r, g, b, a = px[d2xy(k)]
        out += bytes((a, b, g, r))
    return bytes(out)


def patch_package(pkg_raw: bytes, pkg_path: Path, master: Path = MASTER) -> bytes:
    """Return ``pkg_raw`` with the 日 tile replaced in its own zlib slot."""
    slots = tex_slots(pkg_raw, pkg_path)
    if NAME not in slots:
        raise SystemExit(f"pkg {PKG}: {NAME} missing")
    w, h, fmt, dec_len, is_cmp, cmp_len, cmp_off = slots[NAME]
    if (w, h) != SIZE or fmt != FMT_RGBA8 or not is_cmp or dec_len != w * h * 4:
        raise SystemExit(f"{NAME}: unexpected TEX (fmt={fmt}, cmp={is_cmp}, dec_len={dec_len}, {w}x{h})")
    im = Image.open(master)
    if im.size != SIZE:
        raise SystemExit(f"{master.name} is {im.size}, expected {SIZE}")
    slot = try_compress_to_slot(encode_rgba8_tile(im), cmp_len)
    if slot is None:
        raise SystemExit(f"{master.name} does not fit the {cmp_len}-byte zlib slot")
    blob = bytearray(pkg_raw)
    blob[cmp_off : cmp_off + cmp_len] = slot
    return bytes(blob)


def main() -> int:
    if not MOD_IMG.is_file():
        raise SystemExit(f"missing {MOD_IMG}")
    bak = maybe_backup_img(MOD_IMG, "date_day_glyph")
    pkg_dir = OUT / "img_data"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    img = ImgBin(str(_vanilla_src()))
    try:
        img.parse(False)
        res = img.entries[PKG]
        if res is None:
            raise SystemExit(f"pkg {PKG} missing")
        src = pkg_dir / f"vanilla_{PKG:04d}"
        src.write_bytes(res.fw.read())
    finally:
        img.fh.close()
    (pkg_dir / f"new_{PKG:04d}").write_bytes(patch_package(src.read_bytes(), src))

    try:
        for dest in _deploy_targets():
            splice_packages_into_img(dest, pkg_dir, [PKG], dest)
            print("spliced", PKG, "->", dest, flush=True)
    except PackError as exc:
        raise SystemExit(f"splice failed: {exc}") from exc
    print("deployed date-info day mark EN ->", MOD_IMG, flush=True)
    print("Rollback:", bak, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
