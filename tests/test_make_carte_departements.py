"""Tests for tools/design/make_carte_departements.py (map of the departments of Normandy,
normandie/carte.qmd)."""

import json
import re
from pathlib import Path

import check_figures as cf
import make_carte_departements as mc
from check_contrast import parse_scss_tokens

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "normandie-carte.json").read_text(encoding="utf-8"))
TOKENS = parse_scss_tokens((ROOT / "assets" / "theme.scss").read_text(encoding="utf-8"))


def test_map_follows_the_figure_rules():
    assert cf.check_svg(mc.NAME, mc.svg(DATA), TOKENS) == []


def test_each_department_is_drawn_and_named():
    text = mc.svg(DATA)
    for dep in DATA["departements"]:
        assert f'id="{mc.NAME}-dep-{dep["code"]}"' in text
        assert f">{dep['nom']}</text>" in text
        assert f">({dep['code']})</text>" in text


def test_the_two_centres_are_told_apart_by_more_than_colour():
    text = mc.svg(DATA)
    for dep in DATA["departements"]:
        fill = re.search(rf'id="{mc.NAME}-dep-{dep["code"]}" d="[^"]*" fill="([^"]*)"', text).group(1)
        hatched = fill == f"url(#{mc.NAME}-rayures)"
        assert hatched == (dep["crpv"] == "Rouen")


def test_both_centres_are_marked_and_the_legend_names_them():
    text = mc.svg(DATA)
    for centre in ("Caen", "Rouen"):
        assert f">CRPV de {centre}</text>" in text


def test_the_map_is_deterministic_and_the_file_up_to_date():
    assert mc.svg(DATA) == mc.svg(DATA)
    assert mc.OUT.read_text(encoding="utf-8") == mc.svg(DATA)


def test_centroid_of_a_square_and_of_a_flat_ring():
    area, (x, y) = mc.area_and_centroid([(0, 0), (2, 0), (2, 2), (0, 2)])
    assert abs(area) == 4 and (x, y) == (1, 1)
    area, _ = mc.area_and_centroid([(0, 0), (1, 1), (2, 2)])  # an islet simplified to a line
    assert area == 0
