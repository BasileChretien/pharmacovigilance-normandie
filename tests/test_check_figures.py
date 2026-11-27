"""Tests for tools/checks/check_figures.py (the SVG figures and their placement)."""

import check_figures as cf

TOKENS = {
    "pv-ink": "#10283a",
    "pv-paper": "#ffffff",
    "pv-mist": "#eef6fa",
    "pv-cyan": "#19a6e3",
    "pv-signal": "#0a5c9e",
}

GOOD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 120" width="440" height="120"
  font-family="'Atkinson Hyperlegible Next Variable', system-ui, sans-serif" font-size="18" fill="#10283a">
  <defs><pattern id="essai-1-points" width="8" height="8" patternUnits="userSpaceOnUse">
    <circle cx="4" cy="4" r="2" fill="#19a6e3"/></pattern></defs>
  <rect x="0" y="0" width="440" height="120" fill="#eef6fa" stroke="#0a5c9e"/>
  <rect x="300" y="10" width="100" height="100" fill="url(#essai-1-points)"/>
  <text x="20" y="40">Une étiquette</text>
  <g font-size="16"><text x="20" y="80" fill="#0a5c9e">Une autre</text></g>
</svg>"""


def problems(text, name="essai-1"):
    return cf.check_svg(name, text, TOKENS)


# --- the SVG files -----------------------------------------------------------

def test_good_figure_passes():
    assert problems(GOOD) == []


def test_malformed_svg_is_reported():
    assert any("XML" in p for p in problems("<svg><text>sans fin</svg>"))


def test_width_above_the_maximum_is_reported():
    text = GOOD.replace('viewBox="0 0 440 120" width="440"', 'viewBox="0 0 600 120" width="600"')
    assert any("largeur" in p for p in problems(text))


def test_width_must_match_the_viewbox():
    text = GOOD.replace('width="440" height="120"\n', 'width="400" height="120"\n')
    assert any("viewBox" in p for p in problems(text))


def test_colour_outside_the_tokens_is_reported():
    text = GOOD.replace('stroke="#0a5c9e"', 'stroke="#ff0000"')
    assert any("#ff0000" in p for p in problems(text))


def test_text_in_a_decorative_colour_is_reported():
    text = GOOD.replace('<text x="20" y="40">', '<text x="20" y="40" fill="#19a6e3">')
    assert any("pv-cyan" in p for p in problems(text))


def test_text_without_a_fill_is_reported():
    text = GOOD.replace(' font-size="18" fill="#10283a">', ' font-size="18">')
    assert any("couleur" in p for p in problems(text))


def test_small_text_is_reported():
    text = GOOD.replace('<g font-size="16">', '<g font-size="12">')
    assert any("12" in p for p in problems(text))


def test_ids_must_start_with_the_figure_name():
    text = GOOD.replace("essai-1-points", "points")
    assert any("points" in p for p in problems(text))


def test_external_link_is_reported():
    text = GOOD.replace('fill="url(#essai-1-points)"', 'fill="url(https://exemple.fr/motif.svg)"')
    assert problems(text)


def test_style_script_and_title_are_reported():
    for extra in ('<style>text{fill:red}</style>', "<script>alert(1)</script>", "<title>Titre</title>"):
        text = GOOD.replace("<defs>", extra + "<defs>")
        assert problems(text), extra


def test_style_attribute_and_opacity_are_reported():
    assert problems(GOOD.replace('<text x="20" y="40">', '<text x="20" y="40" style="fill:red">'))
    assert problems(GOOD.replace('<text x="20" y="40">', '<text x="20" y="40" opacity="0.5">'))


def test_font_family_must_be_the_site_font():
    text = GOOD.replace("'Atkinson Hyperlegible Next Variable', ", "")
    assert any("police" in p for p in problems(text))


# --- the shortcodes in the pages ---------------------------------------------

def test_shortcodes_are_parsed():
    page = 'Texte.\n\n{{< figure-svg notice-1 alt="Une notice" legende="Les six rubriques." >}}\n'
    assert cf.parse_shortcodes(page) == [
        {"nom": "notice-1", "alt": "Une notice", "legende": "Les six rubriques."}
    ]


def test_shortcode_without_alt_or_caption_is_reported():
    page = '{{< figure-svg notice-1 legende="Les six rubriques." >}}'
    assert any("alt" in p for p in cf.check_page(page, {"notice-1"}))
    page = '{{< figure-svg notice-1 alt="Une notice" >}}'
    assert any("legende" in p for p in cf.check_page(page, {"notice-1"}))


def test_shortcode_naming_a_missing_file_is_reported():
    page = '{{< figure-svg absent-1 alt="Une notice" legende="Les six rubriques." >}}'
    assert any("absent-1" in p for p in cf.check_page(page, {"notice-1"}))


def test_figure_used_twice_on_a_page_is_reported():
    one = '{{< figure-svg notice-1 alt="Une notice" legende="Les six rubriques." >}}\n'
    assert cf.check_page(one + one, {"notice-1"})


def test_site_figures_pass(capsys):
    assert cf.main() == 0
    assert "figures conformes" in capsys.readouterr().out
