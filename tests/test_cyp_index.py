"""Tests for tools/build/make_cyp_index.py (per-drug index of the cytochrome table)."""

import make_cyp_index as mk

TABLE = """
| Enzyme ou transporteur | Substrats (exemples) | Inhibiteurs puissants / modérés (exemples) | Inducteurs (exemples) | Conséquence pratique |
|---|---|---|---|---|
| **CYP1A2** | Caféine, clozapine. Prodrogues : codéine (mineure) | Puissants : ciprofloxacine, fluvoxamine. Modérés : éthinylestradiol (contraceptifs oraux) | Puissant : tabac | Exemple |
| **CYP3A4/5** | Simvastatine, clozapine | Puissants : clarithromycine | Puissants : rifampicine ; millepertuis (!) | Exemple |
"""


def test_rows_are_read_by_enzyme():
    rows = mk.parse_table(TABLE)
    assert [r["enzyme"] for r in rows] == ["CYP1A2", "CYP3A4/5"]


def test_names_are_cleaned_and_strength_kept():
    entries = mk.split_cell("Puissants : ciprofloxacine, fluvoxamine. Modérés : éthinylestradiol (contraceptifs oraux)")
    assert entries == [("ciprofloxacine", "puissant"), ("fluvoxamine", "puissant"), ("éthinylestradiol", "modéré")]


def test_index_groups_roles_per_drug():
    index = mk.build_index(mk.parse_table(TABLE))
    assert index["clozapine"] == ["substrat du CYP1A2", "substrat du CYP3A4/5"]
    assert index["rifampicine"] == ["inducteur puissant du CYP3A4/5"]
    assert index["codéine"] == ["substrat du CYP1A2"]
    assert "millepertuis" in index


def test_markdown_is_sorted_alphabetically_ignoring_accents():
    md = mk.to_markdown({"éthinylestradiol": ["x"], "caféine": ["y"], "fluvoxamine": ["z"]})
    lines = [line for line in md.splitlines() if line.startswith("| ") and "Médicament" not in line]
    assert [line.split("|")[1].strip() for line in lines] == ["Caféine", "Éthinylestradiol", "Fluvoxamine"]


def test_names_joined_by_et_are_split_and_pgp_takes_feminine_article():
    assert mk.split_cell("Apixaban et rivaroxaban") == [("apixaban", ""), ("rivaroxaban", "")]
    assert mk._of("P-glycoprotéine (P-gp)") == "de la P-glycoprotéine (P-gp)"


def test_committed_index_matches_the_table():
    """The index included in the page is the one the script draws from the current table."""
    expected = mk.to_markdown(mk.build_index(mk.parse_table(mk.SOURCE.read_text(encoding="utf-8"))))
    assert mk.OUT.read_text(encoding="utf-8") == expected, "run: uv run python tools/build/make_cyp_index.py"
