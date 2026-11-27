"""Medical facts that some figures must keep, found by the reviews of the figure pull
requests. Each test names the page sentence that the figure must not contradict."""

import re
from pathlib import Path

import check_figures as cf

ROOT = Path(__file__).resolve().parents[1]


def figure_text(name: str) -> str:
    svg = (ROOT / "assets" / "img" / "figures" / f"{name}.svg").read_text(encoding="utf-8")
    return " ".join(re.findall(r">([^<]+)</t(?:ext|span)>", svg))


def shortcode(page: str, name: str) -> dict[str, str]:
    text = (ROOT / page).read_text(encoding="utf-8")
    return next(code for code in cf.parse_shortcodes(text) if code["nom"] == name)


def test_the_two_hour_rule_is_given_for_levofloxacin_only():
    # Page: « au moins 2 heures avant ou après la lévofloxacine »; ciprofloxacin has
    # another interval (RCP: 1 to 2 hours before or at least 4 hours after).
    code = shortcode("medicaments/classes/fluoroquinolones.qmd", "fluoroquinolones-1")
    assert "lévofloxacine" in figure_text("fluoroquinolones-1")
    assert "lévofloxacine" in code["alt"]
    assert "lévofloxacine" in code["legende"]


def test_the_cystitis_tree_sends_risk_situations_and_warning_signs_to_a_doctor():
    # Page: « On parle de cystite simple quand il n'y a pas de fièvre ni de situation à
    # risque »; the single dose of fosfomycin is for a simple cystitis only. The « Quand
    # consulter » box adds signs that come back within 2 weeks (« consultez ») and great
    # weakness, confusion or mottled skin (« appelez le 15 »).
    text = figure_text("cystite-1")
    code = shortcode("medicaments/maux-courants/cystite.qmd", "cystite-1")
    for words in ("situation à risque", "grossesse", "anomalie des voies urinaires",
                  "reins qui fonctionnent très mal", "défenses immunitaires très affaiblies",
                  "75 ans", "2 semaines", "appelez le 15", "douleur dans le dos"):
        assert words in text, words
        assert words in code["description"], words
    assert "situation à risque" in code["alt"]
