"""Tests for tools/build/make_cytochromes.py (grid and two-drug checker of bon-usage/cytochromes.qmd).

One hand-written source, data/cytochromes.yml, gives both the HUG-style grid and the data
of the checker: these tests hold the parser to its schema, the outputs to their structure,
and the committed outputs to the current data.
"""

import json
import re

import pytest

import make_cytochromes as mk

YAML = """
sources:
  hug: {court: HUG, long: "la carte des HUG (mars 2020)"}
  thesaurus: {court: Thésaurus, long: "la liste du Thésaurus de l'ANSM (septembre 2023)"}
source_par_defaut: hug
medicaments:
  warfarine:
    substrat: {CYP2C9: majeure, CYP1A2: mineure}
  fluconazole:
    inhibiteur: {CYP2C9: puissant, CYP2C19: puissant, CYP3A4/5: puissant}
  codéine:
    substrat: {CYP2D6: mineure prodrogue}
  bupropion:
    substrat: {CYP2B6: majeure métabolite-actif}
    inhibiteur: {CYP2D6: puissant}
  éthinylestradiol:
    précision: contraceptifs oraux
    inhibiteur: {CYP1A2: modéré}
  cobicistat:
    inhibiteur: {CYP3A4/5: puissant thesaurus}
  rifampicine:
    inducteur: {CYP2C9: puissant, P-gp: puissant, CYP2B6: modéré}
"""


def data():
    return mk.load(YAML)


def drug(d, name):
    return next(m for m in d["medicaments"] if m["nom"] == name)


# ---------- Parsing and validation ------------------------------------------


def test_drugs_are_sorted_ignoring_accents_and_capitalised():
    names = [m["nom"] for m in data()["medicaments"]]
    assert names == ["Bupropion", "Cobicistat", "Codéine", "Éthinylestradiol", "Fluconazole", "Rifampicine", "Warfarine"]


def test_substrate_cells_keep_pathway_and_flags():
    d = data()
    assert drug(d, "Codéine")["roles"]["CYP2D6"]["substrat"] == {
        "voie": "mineure", "prodrogue": True, "actif": False, "source": "hug"}
    assert drug(d, "Bupropion")["roles"]["CYP2B6"]["substrat"]["actif"] is True
    assert drug(d, "Warfarine")["roles"]["CYP1A2"]["substrat"]["voie"] == "mineure"


def test_inhibitor_and_inducer_cells_keep_strength_and_source():
    d = data()
    assert drug(d, "Fluconazole")["roles"]["CYP2C9"] == {"inhibiteur": {"force": "puissant", "source": "hug"}}
    assert drug(d, "Cobicistat")["roles"]["CYP3A4/5"]["inhibiteur"] == {"force": "puissant", "source": "thesaurus"}
    assert drug(d, "Rifampicine")["roles"]["CYP2B6"]["inducteur"]["force"] == "modéré"


def test_roles_follow_the_enzyme_order():
    roles = drug(data(), "Rifampicine")["roles"]
    assert list(roles) == ["CYP2B6", "CYP2C9", "P-gp"]


def test_precision_is_kept_apart_from_the_name():
    m = drug(data(), "Éthinylestradiol")
    assert m["precision"] == "contraceptifs oraux"
    assert drug(data(), "Warfarine")["precision"] == ""


@pytest.mark.parametrize("bad, message", [
    ("  x:\n    substrat: {CYP2E1: majeure}\n", "CYP2E1"),
    ("  x:\n    substrat: {CYP2C9: forte}\n", "forte"),
    ("  x:\n    inhibiteur: {CYP2C9: majeure}\n", "majeure"),
    ("  x:\n    inducteur: {CYP2C9: puissant fda}\n", "fda"),
    ("  x:\n    inhibiteur: {CYP2C9: puissant modéré}\n", "modéré"),
    ("  x:\n    substrat: {CYP2C9: prodrogue}\n", "prodrogue"),
    ("  x:\n    cible: {CYP2C9: puissant}\n", "cible"),
    ("  x: {}\n", "x"),
    ("  Warfarine:\n    substrat: {CYP2C9: majeure}\n", "Warfarine"),
])
def test_invalid_entries_are_refused_with_a_clear_message(bad, message):
    with pytest.raises(ValueError, match=re.escape(message)):
        mk.load(YAML + bad)


def test_a_drug_written_twice_is_refused_not_silently_dropped():
    """yaml.safe_load keeps the last of two equal keys: the first entry would vanish."""
    with pytest.raises(ValueError, match="warfarine"):
        mk.load(YAML + "  warfarine:\n    inducteur: {CYP2C9: puissant}\n")


def test_an_enzyme_written_twice_in_one_role_is_refused():
    with pytest.raises(ValueError, match=re.escape("CYP2C9")):
        mk.load(YAML + "  x:\n    substrat: {CYP2C9: majeure, CYP2C9: mineure}\n")


def test_names_that_differ_only_by_punctuation_are_duplicates():
    """The checker's search key (assets/js/cyp-verificateur.js, fold) drops punctuation too."""
    assert mk.fold("Chardon-Marie") == mk.fold("chardon marie") == "chardon marie"
    with pytest.raises(ValueError, match="en double"):
        mk.load(YAML + "  chardon-marie:\n    inhibiteur: {CYP2C8: puissant}\n"
                       "  chardon marie:\n    inhibiteur: {CYP2C8: puissant}\n")


GOOD_DRUG = "medicaments: {a: {substrat: {CYP2D6: majeure}}}\n"


@pytest.mark.parametrize("text, message", [
    ("sources: {hug: {long: x}}\nsource_par_defaut: hug\n" + GOOD_DRUG, "court"),
    ("sources: {hug: {court: HUG}}\nsource_par_defaut: hug\n" + GOOD_DRUG, "long"),
    ("sources: [hug]\nsource_par_defaut: hug\n" + GOOD_DRUG, "sources"),
    ("sources: {hug: {court: HUG, long: x}}\nsource_par_defaut: hug\nmedicaments: [a, b]\n", "medicaments"),
])
def test_malformed_sections_give_a_clear_message(text, message):
    with pytest.raises(ValueError, match=message):
        mk.load(text)


# ---------- Checker data ------------------------------------------------------


def checker(d=None):
    text = mk.to_checker_include(d or data())
    match = re.search(r'<script type="application/json" id="cyp-donnees">(.*?)</script>', text, re.DOTALL)
    assert match, "the data must sit in a JSON script element"
    return json.loads(match.group(1))


def test_checker_data_lists_every_enzyme_with_article_and_anchor():
    enzymes = checker()["enzymes"]
    assert [e["id"] for e in enzymes] == list(mk.ENZYMES)
    cyp = next(e for e in enzymes if e["id"] == "CYP3A4/5")
    pgp = next(e for e in enzymes if e["id"] == "P-gp")
    assert cyp["de"] == "du CYP3A4/5" and cyp["ancre"] == "exemples-cyp3a4-5"
    assert pgp["de"] == "de la P-gp" and pgp["ancre"] == "exemples-p-gp"


def test_checker_data_holds_the_same_roles_as_the_grid():
    d = data()
    assert checker(d)["medicaments"] == d["medicaments"]
    assert checker(d)["sources"]["thesaurus"]["long"].startswith("la liste du Thésaurus")


def test_checker_data_cannot_close_its_script_element():
    d = data()
    d["medicaments"][0]["precision"] = "</script><b>"
    assert "</script><b>" not in mk.to_checker_include(d)
    assert checker(d)["medicaments"][0]["precision"] == "</script><b>"


# ---------- Grid ----------------------------------------------------------------


def tables(md):
    return re.findall(r"<table class=\"cyp-grille\">.*?</table>", md, re.DOTALL)


def test_grid_has_three_tables_substrates_inhibitors_inducers_with_captions():
    md = mk.to_grid(data())
    ids = re.findall(r'<div id="(grille-[a-z]+)" class="cyp-grille-cadre"', md)
    assert ids == ["grille-substrats", "grille-inhibiteurs", "grille-inducteurs"]
    captions = re.findall(r"<caption>(Tableau \d\. \w+)", md)
    assert captions == ["Tableau 1. Substrats", "Tableau 2. Inhibiteurs", "Tableau 3. Inducteurs"]
    assert len(tables(md)) == 3


def test_grid_has_no_heading_inside_the_filter_box():
    """A heading inside a div drops out of the table of contents (tools/checks/check_toc.py)."""
    assert not re.search(r"^#", mk.to_grid(data()), re.MULTILINE)


def test_grid_columns_are_the_enzymes():
    first = tables(mk.to_grid(data()))[0]
    heads = re.findall(r'<th scope="col"[^>]*>(.*?)</th>', first)
    assert heads == ["Médicament", *mk.ENZYMES]


def test_each_table_lists_only_drugs_with_that_role():
    subst, inhib, induc = tables(mk.to_grid(data()))
    rows = lambda t: re.findall(r'<th scope="row">([^<]+)', t)
    assert [r.strip() for r in rows(subst)] == ["Bupropion", "Codéine", "Warfarine"]
    assert [r.strip() for r in rows(inhib)] == ["Bupropion", "Cobicistat", "Éthinylestradiol", "Fluconazole"]
    assert [r.strip() for r in rows(induc)] == ["Rifampicine"]


def row(table, name):
    match = re.search(r'<tr><th scope="row">' + re.escape(name) + r"\b.*?</tr>", table, re.DOTALL)
    assert match, name
    return re.findall(r"<td[^>]*>(.*?)</td>", match.group(0), re.DOTALL)


def test_strength_is_written_in_words_not_only_in_colour():
    subst, inhib, induc = tables(mk.to_grid(data()))
    flu = row(inhib, "Fluconazole")
    assert len(flu) == len(mk.ENZYMES)
    assert "Puissant" in flu[mk.ENZYMES.index("CYP2C9")]
    assert flu[mk.ENZYMES.index("CYP1A2")] == ""
    assert "Modéré" in row(inhib, "Éthinylestradiol")[0]
    assert "Modéré" in row(induc, "Rifampicine")[mk.ENZYMES.index("CYP2B6")]
    codeine = row(subst, "Codéine")[mk.ENZYMES.index("CYP2D6")]
    assert "Mineure" in codeine and "prodrogue" in codeine
    assert "métabolite actif" in row(subst, "Bupropion")[mk.ENZYMES.index("CYP2B6")]
    assert "Majeure" in row(subst, "Warfarine")[mk.ENZYMES.index("CYP2C9")]


def test_strong_and_moderate_cells_have_distinct_classes():
    inhib = tables(mk.to_grid(data()))[1]
    assert re.search(r'<td class="cyp-fort">\s*<span class="cyp-marque">Puissant', inhib)
    assert re.search(r'<td class="cyp-moyen">\s*<span class="cyp-marque">Modéré', inhib)


def test_an_entry_from_another_source_names_it_in_its_cell():
    inhib = tables(mk.to_grid(data()))[1]
    cell = row(inhib, "Cobicistat")[mk.ENZYMES.index("CYP3A4/5")]
    assert "Thésaurus" in cell
    assert "HUG" not in row(inhib, "Fluconazole")[mk.ENZYMES.index("CYP2C9")]


def test_precision_is_shown_beside_the_name():
    inhib = tables(mk.to_grid(data()))[1]
    assert re.search(r'Éthinylestradiol <span class="cyp-precision">\(contraceptifs oraux\)</span>', inhib)


def test_scrolling_box_is_a_named_focusable_region():
    md = mk.to_grid(data())
    boxes = re.findall(r'<div id="grille-[a-z]+" class="cyp-grille-cadre" role="region" aria-label="([^"]+)" tabindex="0">', md)
    assert len(boxes) == 3 and all(boxes)


def test_text_is_html_escaped():
    d = data()
    d["medicaments"][0]["precision"] = "a < b & c"
    assert "(a &lt; b &amp; c)" in mk.to_grid(d)


# ---------- Real data and committed outputs -------------------------------------


@pytest.fixture(scope="module")
def real():
    return mk.load(mk.SOURCE.read_text(encoding="utf-8"))


def roles_of(real, name):
    return drug(real, name)["roles"]


def test_real_data_keeps_the_classifications_of_the_former_table(real):
    """Spot checks of the table as it was before the grid (25 and 28/11/2026 reading of the HUG card)."""
    assert roles_of(real, "Fluconazole")["CYP2C9"]["inhibiteur"]["force"] == "puissant"
    assert roles_of(real, "Fluoxétine")["CYP2C19"]["inhibiteur"]["force"] == "modéré"
    assert roles_of(real, "Fluoxétine")["CYP2D6"]["inhibiteur"]["force"] == "puissant"
    assert roles_of(real, "Codéine")["CYP2D6"]["substrat"] == {
        "voie": "mineure", "prodrogue": True, "actif": False, "source": "hug"}
    assert roles_of(real, "Tamoxifène")["CYP2D6"]["substrat"]["prodrogue"] is True
    assert roles_of(real, "Apixaban")["CYP3A4/5"]["substrat"]["voie"] == "mineure"
    assert roles_of(real, "Apixaban")["P-gp"]["substrat"]["voie"] == "majeure"
    assert roles_of(real, "Bupropion")["CYP2B6"]["substrat"]["actif"] is True
    assert roles_of(real, "Cobicistat")["CYP3A4/5"]["inhibiteur"]["source"] == "thesaurus"
    assert set(roles_of(real, "Éfavirenz")["CYP2B6"]) == {"substrat", "inhibiteur", "inducteur"}


def test_clopidogrel_is_a_minor_cyp2c19_substrate_with_active_metabolite(real):
    """HUG card, table 1 (light cell with "!"), read on 28/11/2026: the example of the page
    (clopidogrel + omeprazole, Plavix SmPC) rests on this pathway."""
    assert roles_of(real, "Clopidogrel")["CYP2C19"]["substrat"] == {
        "voie": "mineure", "prodrogue": True, "actif": False, "source": "hug"}


def test_real_data_has_no_cyp2d6_inducer_and_no_pseudo_drug(real):
    assert not any("inducteur" in m["roles"].get("CYP2D6", {}) for m in real["medicaments"])
    assert not any(m["nom"].lower().startswith("pas ") for m in real["medicaments"])


def test_real_data_counts(real):
    """Entries per role: 92 substrates, 82 inhibitors and 51 inducers in the former table,
    plus clopidogrel (CYP2C19); 129 drugs."""
    count = lambda role: sum(role in r for m in real["medicaments"] for r in m["roles"].values())
    assert (count("substrat"), count("inhibiteur"), count("inducteur")) == (93, 82, 51)
    assert len(real["medicaments"]) == 129


def test_every_enzyme_anchor_exists_on_the_page():
    page = mk.PAGE.read_text(encoding="utf-8")
    for enzyme in mk.ENZYMES:
        assert "{#" + mk.anchor(enzyme) + "}" in page, enzyme


def test_page_includes_the_outputs_and_loads_the_checker():
    page = mk.PAGE.read_text(encoding="utf-8")
    assert "{{< include ../_includes/cyp-grille.md >}}" in page
    assert "{{< include ../_includes/cyp-donnees.md >}}" in page
    assert '<script src="../assets/js/cyp-verificateur.js" defer></script>' in page
    assert "cyp-index.md" not in page


def test_committed_outputs_match_the_data(real):
    assert mk.OUT_GRID.read_text(encoding="utf-8") == mk.to_grid(real), "run: uv run python tools/build/make_cytochromes.py"
    assert mk.OUT_DATA.read_text(encoding="utf-8") == mk.to_checker_include(real), "run: uv run python tools/build/make_cytochromes.py"
