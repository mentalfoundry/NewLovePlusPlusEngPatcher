"""English UI text does not use the Japanese long-vowel mark ー ("coldー")."""

from __future__ import annotations

import json
import re

from conftest import ROOT

# ー touching Latin text: a stretched English word, not a quoted Japanese term.
STRETCHED = re.compile(r"[A-Za-z.,!?！？]ー|ー[A-Za-z]")


def test_no_english_value_stretches_with_the_long_vowel_mark():
    path = ROOT / "assets" / "textresource" / "translations.json"
    table = json.loads(path.read_text(encoding="utf-8"))["translations"]
    bad = {jp: en for jp, en in table.items() if STRETCHED.search(en)}
    assert bad == {}
