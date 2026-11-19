"""Community a*/k* English mapped onto the NLP_01 / NLP_02 script packs."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import TOOLS, load_module

import patch_names as names
import script_inject

cp = load_module("build_community_packs", TOOLS / "build_community_packs.py")


def script(entries: list[list[str]], key: int = 1, skey: int = 2) -> bytes:
    """DBN2 with one entry per dialog list; ``key`` / ``skey`` stand for the per-pack keys."""
    return names.build_dbin2(
        key, 0, [names.DbinEntry(i, i, names.SDL2Data(skey, [], d)) for i, d in enumerate(entries)]
    )


JP = [["こんにちは。\n元気？", "うん"], ["またね"]]
EN = [["Hello.\nHow are you?", "Yeah"], ["See you"]]


def test_map_pack_keeps_pack_keys_and_takes_english():
    pack = script([["こんにちは。　元気？", "うん"], ["またね"]], key=7, skey=9)
    out, why = cp.map_pack(script(EN), script(JP), pack)
    assert why == ""
    key, _unknown, entries = names.parse_dbin2(out)
    assert key == 7
    assert [e.sdl2.key for e in entries] == [9, 9]
    assert [e.sdl2.dialogs for e in entries] == EN


def test_map_pack_takes_a_shorter_pack():
    out, _ = cp.map_pack(script(EN), script(JP), script(JP[:1]))
    assert [e.sdl2.dialogs for e in names.parse_dbin2(out)[2]] == EN[:1]


def test_map_pack_accepts_typo_level_variants():
    pack = script([["こんにちわ。元気？", "うん"], ["またね"]])
    assert cp.map_pack(script(EN), script(JP), pack)[1] == ""


@pytest.mark.parametrize(
    ("english", "pack", "why"),
    [
        (EN[:1], JP, "shape"),
        (EN, JP + [["余分"]], "3 entries, script has 2"),
        (EN, [["こんにちは。", "うん", "え"], ["またね"]], "entry 0: no English for pack line 'え'"),
        (EN, [["こんにちは。元気？", "まったく別の台詞です"], ["またね"]], "no English for pack line"),
    ],
)
def test_map_pack_refuses_lines_that_do_not_line_up(english, pack, why):
    out, reason = cp.map_pack(script(english), script(JP), script(pack))
    assert out is None
    assert why in reason


def _tree(tmp_path: Path) -> tuple[Path, Path]:
    dbin, vanilla = tmp_path / "rebuild_dbin2", tmp_path / "vanilla"
    for pack in ("script", "NLP_01", "NLP_02"):
        (dbin / pack).mkdir(parents=True)
        (vanilla / pack).mkdir(parents=True)
    for stem in ("k002", "a027", "t001", "k999"):
        (dbin / "script" / f"{stem}.dbin2").write_bytes(script(EN))
        (vanilla / "script" / f"{stem}.dbin2").write_bytes(script(JP))
    (vanilla / "NLP_01" / "k002.dbin2").write_bytes(script(JP, key=5))
    (vanilla / "NLP_02" / "k002.dbin2").write_bytes(script(JP, key=6))
    (vanilla / "NLP_01" / "a027.dbin2").write_bytes(script([["別の文です", "うん"], ["またね"]]))
    (vanilla / "NLP_01" / "t001.dbin2").write_bytes(script(JP))
    (vanilla / "NLP_01" / "k999.dbin2").write_bytes(script(JP))
    return dbin, vanilla


def test_main_writes_aligned_community_stems(tmp_path, monkeypatch, capsys):
    dbin, vanilla = _tree(tmp_path)
    monkeypatch.setattr(script_inject, "community_stems", lambda: {"k002", "a027"})
    contrib = tmp_path / "contrib"
    (contrib / "script").mkdir(parents=True)
    (contrib / "script" / "a027.dbin2").write_bytes(script(EN))  # reviewed, but NLP_01 has another line
    args = ["--dbin", str(dbin), "--vanilla-bin", str(vanilla), "--contrib", str(contrib)]
    assert cp.main([*args, "--check"]) == 0
    assert not (dbin / "NLP_01" / "k002.dbin2").exists()
    assert cp.main(args) == 0
    out = capsys.readouterr().out
    assert "can write 2 pack file(s)" in out and "wrote 2 pack file(s)" in out
    assert out.count("skipped NLP_01/a027: entry 0: no English for pack line '別の文です'") == 4  # 2 runs x 2 builds
    for pack, key in (("NLP_01", 5), ("NLP_02", 6)):
        k, _u, entries = names.parse_dbin2((dbin / pack / "k002.dbin2").read_bytes())
        assert k == key and [e.sdl2.dialogs for e in entries] == EN
    assert not (dbin / "NLP_01" / "a027.dbin2").exists()
    assert not (dbin / "NLP_01" / "t001.dbin2").exists()  # Manaka is not community
    assert not (dbin / "NLP_01" / "k999.dbin2").exists()  # not in the manifest


def test_realign_maps_shared_lines_and_fills_pack_only_ones(monkeypatch):
    monkeypatch.setattr(cp, "PACK_ONLY_LINES", {"追加": "Extra"})
    js = names.parse_dbin2(script([["一", "二", "三つです"], ["四"]]))[2]
    en = names.parse_dbin2(script([["One", "Two", "Three"], ["Four"]]))[2]
    jp = names.parse_dbin2(script([["一", "追加", "三つです"], []]))[2]  # 二 replaced, 四 dropped
    assert cp.realign(js, jp, en) == ([["One", "Extra", "Three"], []], "")
    jp = names.parse_dbin2(script([["一", "二", "三つです", "追加"], ["四"]]))[2]  # inserted line
    assert cp.realign(js, jp, en) == ([["One", "Two", "Three", "Extra"], ["Four"]], "")
    jp = names.parse_dbin2(script([["一", "二", "三つです！"], ["四"]]))[2]  # typo-level replace
    assert cp.realign(js, jp, en)[0] == [["One", "Two", "Three"], ["Four"]]
    assert cp.realign(js, jp[:1], en) == (None, "1 entries, script has 2")


def test_map_pack_falls_back_to_realign(monkeypatch):
    monkeypatch.setattr(cp, "PACK_ONLY_LINES", {"追加": "Extra"})
    out, why = cp.map_pack(script(EN), script(JP), script([["こんにちは。元気？", "追加", "うん"], ["またね"]], key=4))
    assert why == ""
    key, _u, entries = names.parse_dbin2(out)
    assert key == 4 and [e.sdl2.dialogs for e in entries] == [["Hello.\nHow are you?", "Extra", "Yeah"], ["See you"]]


def _contrib_tree(tmp_path: Path) -> tuple[Path, Path]:
    contrib, vanilla = tmp_path / "contrib", tmp_path / "vanilla"
    for pack in ("script", "NLP_01", "NLP_02"):
        (contrib / pack).mkdir(parents=True)
        (vanilla / pack).mkdir(parents=True)
    for stem in ("a001", "a002", "a003", "a004"):
        (contrib / "script" / f"{stem}.dbin2").write_bytes(script(EN))
        (vanilla / "script" / f"{stem}.dbin2").write_bytes(script(JP))
        (vanilla / "NLP_01" / f"{stem}.dbin2").write_bytes(script(JP, key=5))
    (contrib / "NLP_01" / "a002.dbin2").write_bytes(b"hand-made")  # own pack file: kept
    (vanilla / "NLP_01" / "a003.dbin2").write_bytes(script([["別の文です", "うん"], ["またね"]]))
    (vanilla / "script" / "a004.dbin2").unlink()  # no script JP to align against
    return contrib, vanilla


def test_build_contrib_mirrors_reviewed_stems(tmp_path):
    contrib, vanilla = _contrib_tree(tmp_path)
    assert cp.build_contrib(contrib, vanilla, write=False) == (1, ["NLP_01/a003: entry 0: no English for pack line '別の文です'"])
    assert not (contrib / "NLP_01" / "a001.dbin2").exists()
    done, _skipped = cp.build_contrib(contrib, vanilla, write=True)
    assert done == 1
    k, _u, entries = names.parse_dbin2((contrib / "NLP_01" / "a001.dbin2").read_bytes())
    assert k == 5 and [e.sdl2.dialogs for e in entries] == EN
    assert (contrib / "NLP_01" / "a002.dbin2").read_bytes() == b"hand-made"
    assert __import__("json").loads((contrib / "pack_mirrors.json").read_text()) == ["NLP_01/a001"]
    # A listed mirror is rebuilt from the reviewed file, and dropped once it no longer lines up.
    (contrib / "script" / "a001.dbin2").write_bytes(script([["Hi.", "Yes"], ["Bye"]]))
    cp.build_contrib(contrib, vanilla, write=True)
    assert names.parse_dbin2((contrib / "NLP_01" / "a001.dbin2").read_bytes())[2][1].sdl2.dialogs == ["Bye"]
    (vanilla / "NLP_01" / "a001.dbin2").write_bytes(script([["別の文です", "うん"], ["またね"]]))
    cp.build_contrib(contrib, vanilla, write=True)
    assert not (contrib / "NLP_01" / "a001.dbin2").exists()
    assert __import__("json").loads((contrib / "pack_mirrors.json").read_text()) == []


def test_shipped_mirrors_are_listed_and_in_place():
    listed = __import__("json").loads(cp.MIRRORS.read_text(encoding="utf-8"))
    assert listed and all((cp.CONTRIB / key).with_suffix(".dbin2").is_file() for key in listed)


def test_without_a_manifest_every_a_k_stem_is_community(tmp_path, monkeypatch):
    dbin, _vanilla = _tree(tmp_path)
    monkeypatch.setattr(script_inject, "community_stems", lambda: set())
    assert cp.community_english(dbin) == ["a027", "k002", "k999"]


def test_main_needs_the_vanilla_tree(tmp_path):
    with pytest.raises(SystemExit, match="missing vanilla script tree"):
        cp.main(["--vanilla-bin", str(tmp_path / "none")])


@pytest.mark.local_data
def test_shipped_pack_files_match_a_fresh_build(tmp_path):
    """rebuild_dbin2/NLP_0x community files are current with rebuild_dbin2/script."""
    if not (cp.VANILLA_BIN / "script").is_dir():
        pytest.skip("no vanilla script tree")
    dbin = tmp_path / "dbin"
    (dbin / "script").mkdir(parents=True)
    for stem in cp.community_english(cp.DBIN):
        (dbin / "script" / f"{stem}.dbin2").write_bytes((cp.DBIN / "script" / f"{stem}.dbin2").read_bytes())
    done, _skipped = cp.build(dbin, cp.VANILLA_BIN, write=True, pack_only=cp.load_pack_only())
    assert done > 0
    for path in sorted((dbin / "NLP_01").glob("*.dbin2")) + sorted((dbin / "NLP_02").glob("*.dbin2")):
        assert (cp.DBIN / path.parent.name / path.name).read_bytes() == path.read_bytes(), path


@pytest.mark.local_data
def test_shipped_mirrors_match_a_fresh_build(tmp_path):
    """assets/script_contrib/dbin2/NLP_0x mirrors are current with the reviewed script files."""
    import json
    import shutil

    if not (cp.VANILLA_BIN / "script").is_dir():
        pytest.skip("no vanilla script tree")
    listed = json.loads(cp.MIRRORS.read_text(encoding="utf-8"))
    contrib = tmp_path / "contrib"
    shutil.copytree(cp.CONTRIB / "script", contrib / "script")
    for pack in cp.PACKS:  # hand-made pack files stay; mirrors are rebuilt
        (contrib / pack).mkdir()
        for path in (cp.CONTRIB / pack).glob("*.dbin2"):
            if f"{pack}/{path.stem}" not in listed:
                shutil.copy(path, contrib / pack / path.name)
    shutil.copy(cp.PACK_ONLY_FILE, contrib / cp.PACK_ONLY_FILE.name)
    cp.build_contrib(contrib, cp.VANILLA_BIN, write=True)
    assert json.loads((contrib / "pack_mirrors.json").read_text(encoding="utf-8")) == listed
    for key in listed:
        assert (contrib / f"{key}.dbin2").read_bytes() == (cp.CONTRIB / f"{key}.dbin2").read_bytes(), key


def test_realign_takes_registry_lines_and_checks_their_markers():
    js = names.parse_dbin2(script([["一", "二"]]))[2]
    en = names.parse_dbin2(script([["One", "Two"]]))[2]
    jp = names.parse_dbin2(script([["一", "別の行", "二"]]))[2]
    assert cp.realign(js, jp, en, {"別の行": "Extra"}) == ([["One", "Extra", "Two"]], "")
    assert cp.realign(js, jp, en, {}) == (None, "entry 0: no English for pack line '別の行'")
    # a nickname marker must survive, in either spelling
    jp = names.parse_dbin2(script([["一", "▲高嶺＊＊▲！", "二"]]))[2]
    assert cp.realign(js, jp, en, {"▲高嶺＊＊▲！": "▲Takane＊＊▲！"})[1] == ""
    why = cp.realign(js, jp, en, {"▲高嶺＊＊▲！": "Takane！"})[1]
    assert why.startswith("entry 0: markers of")


def test_realign_pairs_entries_when_the_pack_drops_or_adds_one():
    js = names.parse_dbin2(script([["一"], ["二"], [], ["四"]]))[2]
    en = names.parse_dbin2(script([["One"], ["Two"], [], ["Four"]]))[2]
    jp = names.parse_dbin2(script([["一"], [], ["四"]]))[2]  # 二 and one empty entry dropped
    assert cp.realign(js, jp, en)[0] is None  # refused unless asked
    assert cp.realign(js, jp, en, {}, align_entries=True)[0] == [["One"], [], ["Four"]]
    jp = names.parse_dbin2(script([["一"], ["新"], ["二"], [], ["四"]]))[2]  # an entry only the pack has
    assert cp.realign(js, jp, en, {"新": "New"}, align_entries=True)[0] == [["One"], ["New"], ["Two"], [], ["Four"]]


def test_map_pack_reads_the_stems_own_registry_entry():
    pack = script([["こんにちは。元気？", "追加", "うん"], ["またね"]])
    assert cp.map_pack(script(EN), script(JP), pack)[0] is None
    reg = {"a001": {"lines": {"追加": "Extra"}}}
    assert cp.map_pack(script(EN), script(JP), pack, "a001", reg)[1] == ""
    assert cp.map_pack(script(EN), script(JP), pack, "a002", reg)[0] is None  # another stem's lines


def test_build_rebuild_maps_registry_stems_and_leaves_matching_files(tmp_path):
    dbin, contrib, vanilla = tmp_path / "dbin", tmp_path / "contrib", tmp_path / "vanilla"
    for d in (dbin / "script", dbin / "NLP_01", contrib / "script", vanilla / "script", vanilla / "NLP_01"):
        d.mkdir(parents=True)
    pack_jp = script([["こんにちは。元気？", "追加", "うん"], ["またね"]], key=5)
    for stem in ("t001", "t002", "t003"):
        (dbin / "script" / f"{stem}.dbin2").write_bytes(script(EN))
        (vanilla / "script" / f"{stem}.dbin2").write_bytes(script(JP))
        (vanilla / "NLP_01" / f"{stem}.dbin2").write_bytes(pack_jp)
    (contrib / "script" / "t003.dbin2").write_bytes(script(EN))  # has a contributor file: build_contrib's job
    reg = {stem: {"lines": {"追加": "Extra"}} for stem in ("t001", "t002", "t003", "t004")}
    done, skipped = cp.build_rebuild(dbin, contrib, vanilla, write=True, pack_only=reg)
    assert (done, skipped) == (2, [])
    key, _u, entries = names.parse_dbin2((dbin / "NLP_01" / "t001.dbin2").read_bytes())
    assert key == 5 and entries[0].sdl2.dialogs == ["Hello.\nHow are you?", "Extra", "Yeah"]
    assert not (dbin / "NLP_01" / "t003.dbin2").exists()
    # same dialogs, different bytes: a matching file is not rewritten
    other = names.build_dbin2(9, 9, names.parse_dbin2((dbin / "NLP_01" / "t002.dbin2").read_bytes())[2])
    (dbin / "NLP_01" / "t002.dbin2").write_bytes(other)
    cp.build_rebuild(dbin, contrib, vanilla, write=True, pack_only=reg)
    assert (dbin / "NLP_01" / "t002.dbin2").read_bytes() == other


@pytest.mark.local_data
def test_every_registry_stem_maps_onto_both_packs():
    """No stem in pack_only_lines.json is left with a pack line it cannot translate."""
    if not (cp.VANILLA_BIN / "script").is_dir():
        pytest.skip("no vanilla script tree")
    reg = cp.load_pack_only()
    assert reg
    _n, skipped = cp.build_contrib(cp.CONTRIB, cp.VANILLA_BIN, write=False)
    _n2, skipped2 = cp.build_rebuild(cp.DBIN, cp.CONTRIB, cp.VANILLA_BIN, write=False, pack_only=reg)
    assert [x for x in skipped + skipped2 if x.split(": ")[0].split("/")[1] in reg] == []
    for stem, cfg in reg.items():  # every translation keeps the Japanese line's markers
        for jp, en in cfg["lines"].items():
            assert cp._tokens(en) == cp._tokens(jp), (stem, jp)


@pytest.mark.local_data
def test_every_shipped_nlp_line_traces_to_reviewed_english():
    """The NLP_01 / NLP_02 file a build ships (contributor, else rebuild_dbin2) has, for each of its
    Japanese lines, either the reviewed script-pack English for that line or its registry translation.
    This keeps an older-draft or extra pack line from showing another line's English."""
    import difflib
    import re

    vanilla = cp.VANILLA_BIN
    if not (vanilla / "script").is_dir():
        pytest.skip("no vanilla script tree")
    reg = cp.load_pack_only()

    def canon(text: str) -> str:
        for form, short in cp._NAME_FORMS:
            text = text.replace(form, short)
        return re.sub(r"\s+", "", text)

    def source(pack: str, stem: str) -> Path | None:
        for root in (cp.CONTRIB / pack, cp.DBIN / pack):
            if (root / f"{stem}.dbin2").is_file():
                return root / f"{stem}.dbin2"
        return None

    bad = []
    for jp_script_path in sorted((vanilla / "script").glob("*.dbin2")):
        stem = jp_script_path.stem
        en_script = source("script", stem)
        if en_script is None:
            continue
        lines = {**cp.PACK_ONLY_LINES, **reg.get(stem, {}).get("lines", {})}
        want = {canon(v): k for k, v in lines.items()}
        js = names.parse_dbin2(jp_script_path.read_bytes())[2]
        es = names.parse_dbin2(en_script.read_bytes())[2]
        for pack in cp.PACKS:
            jp_pack, en_pack = vanilla / pack / f"{stem}.dbin2", source(pack, stem)
            if not jp_pack.is_file() or en_pack is None:
                continue
            jp = names.parse_dbin2(jp_pack.read_bytes())[2]
            ep = names.parse_dbin2(en_pack.read_bytes())[2]
            if len(ep) != len(jp):
                bad.append(f"{pack}/{stem}: {len(ep)} English entries for {len(jp)} Japanese")
                continue
            pairs = [(i, i) for i in range(len(jp))] if len(jp) == len(js) else cp._pair_entries(js, jp)
            for si_e, pi_e in pairs:
                a = [cp._norm(x) for x in js[si_e].sdl2.dialogs] if si_e is not None else []
                eng = es[si_e].sdl2.dialogs if si_e is not None else []
                raw = jp[pi_e].sdl2.dialogs
                b = [cp._norm(x) for x in raw]
                got_all = ep[pi_e].sdl2.dialogs
                if len(got_all) != len(b):
                    bad.append(f"{pack}/{stem}[{pi_e}]: {len(got_all)} English lines for {len(b)} Japanese")
                    continue
                for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                    for k in range(j2 - j1):
                        si, pi = i1 + k, j1 + k
                        got = got_all[pi]
                        same = difflib.SequenceMatcher(None, a[si], b[pi]).ratio() >= cp.MIN_RATIO if op == "replace" and si < i2 else False
                        if op == "equal" or same:
                            if canon(got) != canon(eng[si]):
                                bad.append(f"{pack}/{stem}[{pi_e}.{pi}]: {got!r} is not the script line {eng[si]!r}")
                        elif want.get(canon(got)) not in (raw[pi], b[pi]):
                            bad.append(f"{pack}/{stem}[{pi_e}.{pi}]: pack-only {raw[pi]!r} shows {got!r}")
    assert not bad, f"{len(bad)} NLP lines without reviewed English, e.g.\n" + "\n".join(bad[:15])
