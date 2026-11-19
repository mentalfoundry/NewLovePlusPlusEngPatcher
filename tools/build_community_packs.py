#!/usr/bin/env python3
"""Community Nene / Rinko English for the ``NLP_01`` / ``NLP_02`` script packs.

The game reads each script from one of three packs (``NLP_01``, ``NLP_02``,
``script``; FUN_006ee890 picks it from a per-session byte). The community
``a*`` / ``k*`` English in ``rebuild_dbin2/script`` only ever covered the
``script`` pack, so the same scenes in the other two packs stayed Japanese.

Each pack has its own copy of a stem: the same Japanese lines in the same
order (the packs differ in line breaks, a few typo-level edits, and their file
keys), sometimes with entries missing at the end. This writes
``rebuild_dbin2/<pack>/<stem>.dbin2``: the pack's own vanilla file with each
dialog replaced by the English line at the same entry and dialog index.

A stem is only written for a pack when every line lines up: the pack has no
more entries than ``script``, every entry has the same dialog count, and each
pack line matches the ``script`` Japanese once line breaks are ignored, or
at least ``MIN_RATIO`` alike (typo-level variants; a different sentence or
different choice text fails). Anything else is left out and listed, so the
pack keeps its Japanese or Gemini file.

Reviewed stems get the same treatment: a contributor file
(``assets/script_contrib/dbin2/script/<stem>``) with no file of its own for
``NLP_01`` / ``NLP_02`` is mapped onto that pack too, so the pack shows the
reviewed English instead of Gemini or Japanese. Those generated files are
listed in ``assets/script_contrib/pack_mirrors.json`` and rebuilt on every
run; a hand-made per-pack contributor file is never touched.

Lines only a pack has (older drafts, extra choices) have no script-pack English
to map. Their reviewed English lives in ``assets/script_contrib/dbin2/pack_only_lines.json``
(stem -> ``lines`` {Japanese: English}, optional ``align_entries`` for a pack that drops
or adds a whole entry). Every stem listed there is rebuilt from the script pack's reviewed
English on each run, including the human ``t*`` / ``p*`` stems; a pack line that has
neither a script-pack match nor a registry entry stops that stem and is reported.

  python tools/build_community_packs.py
  python tools/build_community_packs.py --check   # report only
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import script_inject
from patch_names import DbinEntry, SDL2Data, build_dbin2, parse_dbin2

DBIN = ROOT / "rebuild_dbin2"
CONTRIB = script_inject.CONTRIB_DBIN
MIRRORS = CONTRIB / "pack_mirrors.json"
PACK_ONLY_FILE = CONTRIB / "pack_only_lines.json"
VANILLA_BIN = ROOT / "cache" / "vanilla_from_rom" / "romfs" / "script" / "bin"
PACKS = ("NLP_01", "NLP_02")
MIN_RATIO = 0.75


def load_pack_only(path: Path = PACK_ONLY_FILE) -> dict:
    """``{stem: {"lines": {Japanese: English}, "align_entries": bool}}`` ({} when absent)."""
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _norm(text: str) -> str:
    return text.replace("\n", "").replace("　", "")


def misaligned(jp_script: list[DbinEntry], jp_pack: list[DbinEntry]) -> str:
    """Why ``jp_pack`` does not line up with ``jp_script`` ('' when it does)."""
    if len(jp_pack) > len(jp_script):
        return f"{len(jp_pack)} entries, script has {len(jp_script)}"
    for i, (s, p) in enumerate(zip(jp_script, jp_pack)):
        if len(s.sdl2.dialogs) != len(p.sdl2.dialogs):
            return f"entry {i}: {len(p.sdl2.dialogs)} dialogs, script has {len(s.sdl2.dialogs)}"
        for j, (a, b) in enumerate(zip(s.sdl2.dialogs, p.sdl2.dialogs)):
            a, b = _norm(a), _norm(b)
            if a != b and difflib.SequenceMatcher(None, a, b).ratio() < MIN_RATIO:
                return f"entry {i} dialog {j}: {b!r} is not {a!r}"
    return ""


def map_pack(
    english: bytes, jp_script: bytes, jp_pack: bytes, stem: str | None = None, pack_only: dict | None = None
) -> tuple[bytes | None, str]:
    """``(pack file with the English dialogs, '')`` or ``(None, reason)``."""
    _ek, _eu, en = parse_dbin2(english)
    _sk, _su, js = parse_dbin2(jp_script)
    key, unknown, jp = parse_dbin2(jp_pack)
    if [len(e.sdl2.dialogs) for e in en] != [len(e.sdl2.dialogs) for e in js]:
        return None, "English does not match the script pack's shape"
    cfg = (pack_only or {}).get(stem, {})
    align = bool(cfg.get("align_entries"))
    why = misaligned(js, jp)
    if why or (align and len(jp) != len(js)):
        rows, why = realign(js, jp, en, {**PACK_ONLY_LINES, **cfg.get("lines", {})}, align)
        if rows is None:
            return None, why
    else:
        rows = [list(e.sdl2.dialogs) for e in en[: len(jp)]]
    out = [DbinEntry(p.unknown0, p.unknown1, SDL2Data(p.sdl2.key, p.sdl2.unknown, r)) for p, r in zip(jp, rows)]
    return build_dbin2(key, unknown, out), ""


# Lines only the NLP_01 / NLP_02 copy of a stem has, with their English.
PACK_ONLY_LINES = {
    "ごめん。今になってもこっちの制服、少し慣れて無くて。": "Sorry. Even now, I'm still not\nquite used to this uniform.",
    "姉ヶ崎AMAERU": "Anegasaki",  # a032: nameplate variant (sweet voice)
}


_TOKEN_RE = re.compile(r"▲[^▲]*▲|●")
_NAME_FORMS = (("小早川", "K"), ("Kobayaka", "K"), ("高嶺", "T"), ("Takane", "T"), ("姉ヶ崎", "A"), ("Anegasaki", "A"))


def _tokens(text: str) -> list[str]:
    """Name / date markers in ``text``, with a nickname spelled in Japanese or English the same."""
    out = []
    for tok in _TOKEN_RE.findall(text):
        for form, short in _NAME_FORMS:
            tok = tok.replace(form, short)
        out.append(tok)
    return sorted(out)


def _pair_entries(js: list[DbinEntry], jp: list[DbinEntry]) -> list[tuple[int | None, int]]:
    """``(script entry, pack entry)`` in pack order. A script entry the pack dropped is skipped;
    a pack entry with no script twin pairs with ``None``."""
    key = lambda e: tuple(_norm(x) for x in e.sdl2.dialogs)
    pairs: list[tuple[int | None, int]] = []
    sm = difflib.SequenceMatcher(None, [key(e) for e in js], [key(e) for e in jp], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        for k in range(j2 - j1):
            si = i1 + k if op in ("equal", "replace") and i1 + k < i2 else None
            pairs.append((si, j1 + k))
    return pairs


def realign(
    js: list[DbinEntry],
    jp: list[DbinEntry],
    en: list[DbinEntry],
    lines: dict[str, str] | None = None,
    align_entries: bool = False,
) -> tuple[list[list[str]] | None, str]:
    """English rows for a pack whose entries differ in places: per entry, lines
    the pack shares with ``script`` (exact or ``MIN_RATIO`` alike) take the
    script line's English, lines the pack dropped are dropped, and pack-only
    lines come from ``lines`` (default ``PACK_ONLY_LINES``). With ``align_entries``
    a pack that drops or adds a whole entry is paired entry by entry first.
    ``(None, reason)`` when a line has no English or its markers do not match."""
    lines = PACK_ONLY_LINES if lines is None else lines
    if len(jp) != len(js) and not align_entries:
        return None, f"{len(jp)} entries, script has {len(js)}"
    pairs = _pair_entries(js, jp) if align_entries else [(i, i) for i in range(len(jp))]
    rows = []
    for si_entry, pi_entry in pairs:
        p = jp[pi_entry]
        s_lines = [_norm(x) for x in js[si_entry].sdl2.dialogs] if si_entry is not None else []
        e_lines = en[si_entry].sdl2.dialogs if si_entry is not None else []
        a, b = s_lines, [_norm(x) for x in p.sdl2.dialogs]
        row: list[str] = []
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            for k in range(j2 - j1):
                si = i1 + k
                raw = p.sdl2.dialogs[j1 + k]
                if op == "equal" or (op == "replace" and si < i2 and difflib.SequenceMatcher(None, a[si], b[j1 + k]).ratio() >= MIN_RATIO):
                    row.append(e_lines[si])
                elif raw in lines or b[j1 + k] in lines:
                    text = lines.get(raw, lines.get(b[j1 + k]))
                    if _tokens(text) != _tokens(raw):
                        return None, f"entry {pi_entry}: markers of {text!r} differ from {raw!r}"
                    row.append(text)
                else:
                    return None, f"entry {pi_entry}: no English for pack line {b[j1 + k]!r}"
        rows.append(row)
    return rows, ""


def community_english(dbin: Path) -> list[str]:
    """Community a*/k* stems with English in ``dbin/script``."""
    allow = script_inject.community_stems()
    return sorted(
        p.stem
        for p in (dbin / "script").glob("*.dbin2")
        if script_inject.script_prefix(p.stem) in script_inject.COMMUNITY_PREFIXES
        and (not allow or p.stem in allow)
    )


def build(dbin: Path, vanilla: Path, *, write: bool, pack_only: dict | None = None) -> tuple[int, list[str]]:
    """Write (or with ``write=False`` only check) every pack file. Returns
    ``(files written or writable, skipped "pack/stem: reason" lines)``."""
    done, skipped = 0, []
    for stem in community_english(dbin):
        english = (dbin / "script" / f"{stem}.dbin2").read_bytes()
        jp_script = (vanilla / "script" / f"{stem}.dbin2").read_bytes()
        for pack in PACKS:
            src = vanilla / pack / f"{stem}.dbin2"
            if not src.is_file():
                continue
            mapped, why = map_pack(english, jp_script, src.read_bytes(), stem, pack_only)
            if mapped is None:
                skipped.append(f"{pack}/{stem}: {why}")
                continue
            if write:
                dest = dbin / pack / f"{stem}.dbin2"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(mapped)
            done += 1
    return done, skipped


def build_contrib(contrib: Path, vanilla: Path, *, write: bool) -> tuple[int, list[str]]:
    """Mirror each reviewed ``script`` stem onto the packs that have no
    contributor file of their own. Returns ``(files, skipped lines)``."""
    manifest = contrib / MIRRORS.name
    listed = set(json.loads(manifest.read_text(encoding="utf-8"))) if manifest.is_file() else set()
    pack_only = load_pack_only(contrib / PACK_ONLY_FILE.name)
    done, skipped = 0, []
    for english_path in sorted((contrib / "script").glob("*.dbin2")):
        stem = english_path.stem
        jp_script = vanilla / "script" / f"{stem}.dbin2"
        for pack in PACKS:
            src, dest, key = vanilla / pack / f"{stem}.dbin2", contrib / pack / f"{stem}.dbin2", f"{pack}/{stem}"
            if not src.is_file() or not jp_script.is_file() or (dest.is_file() and key not in listed and stem not in pack_only):
                continue
            mapped, why = map_pack(english_path.read_bytes(), jp_script.read_bytes(), src.read_bytes(), stem, pack_only)
            if mapped is None:
                skipped.append(f"{key}: {why}")
                if write and key in listed:
                    dest.unlink(missing_ok=True)
                    listed.discard(key)
                continue
            if write:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(mapped)
                listed.add(key)
            done += 1
    if write:
        manifest.write_text(json.dumps(sorted(listed), indent=1) + "\n", encoding="utf-8")
    return done, skipped


def build_rebuild(dbin: Path, contrib: Path, vanilla: Path, *, write: bool, pack_only: dict | None = None) -> tuple[int, list[str]]:
    """Registry stems with no contributor file (the human ``t*`` / ``p*`` stems and
    community ``a*`` / ``k*`` ones): map ``dbin/script`` English onto ``dbin/<pack>``.
    A pack file whose dialogs already match is left byte for byte as it is."""
    done, skipped = 0, []
    for stem in sorted(pack_only or {}):
        english_path = dbin / "script" / f"{stem}.dbin2"
        if (contrib / "script" / f"{stem}.dbin2").is_file() or not english_path.is_file():
            continue
        jp_script = vanilla / "script" / f"{stem}.dbin2"
        for pack in PACKS:
            src, dest = vanilla / pack / f"{stem}.dbin2", dbin / pack / f"{stem}.dbin2"
            if not src.is_file() or not jp_script.is_file():
                continue
            mapped, why = map_pack(english_path.read_bytes(), jp_script.read_bytes(), src.read_bytes(), stem, pack_only)
            if mapped is None:
                skipped.append(f"{pack}/{stem}: {why}")
                continue
            if write and not (dest.is_file() and _dialogs(dest.read_bytes()) == _dialogs(mapped)):
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(mapped)
            done += 1
    return done, skipped


def _dialogs(data: bytes) -> list[list[str]]:
    return [list(e.sdl2.dialogs) for e in parse_dbin2(data)[2]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dbin", type=Path, default=DBIN)
    ap.add_argument("--vanilla-bin", type=Path, default=VANILLA_BIN)
    ap.add_argument("--contrib", type=Path, default=CONTRIB)
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args(argv)
    if not (args.vanilla_bin / "script").is_dir():
        raise SystemExit(f"missing vanilla script tree: {args.vanilla_bin}")
    pack_only = load_pack_only(args.contrib / PACK_ONLY_FILE.name)
    done, skipped = build(args.dbin, args.vanilla_bin, write=not args.check, pack_only=pack_only)
    print(f"[community-packs] {'can write' if args.check else 'wrote'} {done} pack file(s)")
    for line in skipped:
        print(f"  skipped {line}")
    done, skipped = build_contrib(args.contrib, args.vanilla_bin, write=not args.check)
    print(f"[reviewed-packs] {'can write' if args.check else 'wrote'} {done} pack file(s)")
    for line in skipped:
        print(f"  skipped {line}")
    done, skipped = build_rebuild(args.dbin, args.contrib, args.vanilla_bin, write=not args.check, pack_only=pack_only)
    print(f"[pack-only stems] {'can write' if args.check else 'wrote'} {done} pack file(s)")
    for line in skipped:
        print(f"  skipped {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
