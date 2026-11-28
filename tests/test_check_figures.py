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
  font-family="'Atkinson Hyperlegible Next Variable', system-ui, sans-serif" font-size="18" fill="currentColor">
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
    text = GOOD.replace(' font-size="18" fill="currentColor">', ' font-size="18">')
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


# --- Dark Reader and the dark theme (docs/mode-sombre.md) ---------------------

def test_root_fill_must_be_current_color():
    # Dark Reader darkens a fill set on the <svg> like a background, and the text inherits it.
    text = GOOD.replace('font-size="18" fill="currentColor">', 'font-size="18" fill="#10283a">')
    assert any("currentColor" in p for p in problems(text))


def test_current_color_is_only_for_the_root():
    text = GOOD.replace('fill="#eef6fa" stroke', 'fill="currentColor" stroke')
    assert any("currentColor" in p for p in problems(text))


def test_tspan_with_a_fill_is_reported():
    text = GOOD.replace("<text x=\"20\" y=\"40\">Une étiquette</text>",
                        '<text x="20" y="40">Une <tspan fill="#0a5c9e">étiquette</tspan></text>')
    assert any("tspan" in p for p in problems(text))


def test_tspan_without_a_fill_passes():
    text = GOOD.replace("<text x=\"20\" y=\"40\">Une étiquette</text>",
                        '<text x="20" y="40">Une <tspan font-weight="700">étiquette</tspan></text>')
    assert problems(text) == []


def test_text_coloured_by_its_group_is_reported():
    text = GOOD.replace('<g font-size="16"><text x="20" y="80" fill="#0a5c9e">',
                        '<g font-size="16" fill="#0a5c9e"><text x="20" y="80">')
    assert any("groupe" in p for p in problems(text))


def test_group_fill_is_fine_when_its_text_has_its_own():
    text = GOOD.replace('<g font-size="16">', '<g font-size="16" fill="#eef6fa">')
    assert problems(text) == []


DISC = '<circle cx="60" cy="100" r="14" fill="#10283a"/><text x="60" y="106" text-anchor="middle" fill="#ffffff">1</text>'


def test_text_on_a_small_filled_shape_is_reported():
    # Dark Reader lightens a shape of 32 px or less like a text colour: the number vanishes.
    text = GOOD.replace("</svg>", DISC + "</svg>")
    assert any("petite forme" in p for p in problems(text))


def test_text_on_a_small_outlined_shape_passes():
    disc = DISC.replace('fill="#10283a"/>', 'fill="none" stroke="#10283a" stroke-width="2"/>').replace(
        'fill="#ffffff">1', 'fill="#10283a">1')
    assert problems(GOOD.replace("</svg>", disc + "</svg>")) == []


def test_text_on_a_wide_badge_passes():
    badge = '<rect x="10" y="90" width="106" height="26" fill="#10283a"/><text x="63" y="108" text-anchor="middle" fill="#ffffff">Interdit</text>'
    assert problems(GOOD.replace("</svg>", badge + "</svg>")) == []


def test_small_shape_is_found_through_a_translated_group():
    moved = '<g transform="translate(200 0)">' + DISC + "</g>"
    assert any("petite forme" in p for p in problems(GOOD.replace("</svg>", moved + "</svg>")))


def test_small_shape_elsewhere_than_the_text_passes():
    apart = DISC.replace('<text x="60" y="106"', '<text x="160" y="106"').replace('fill="#ffffff">1', 'fill="#10283a">1')
    assert problems(GOOD.replace("</svg>", apart + "</svg>")) == []


def test_filled_rect_in_a_pattern_is_reported():
    text = GOOD.replace('<circle cx="4" cy="4" r="2" fill="#19a6e3"/>',
                        '<rect width="8" height="8" fill="#eef6fa"/><circle cx="4" cy="4" r="2" fill="#19a6e3"/>')
    assert any("motif" in p for p in problems(text))


def test_dark_map_is_parsed():
    scss = '$pv-figures-sombre: (\n  "#10283a": $pv-ink,\n  "#D3E9F5": #183449,\n);'
    assert cf.parse_dark_map(scss) == {"#10283a": "$pv-ink", "#d3e9f5": "#183449"}


def test_colour_without_a_dark_value_is_reported():
    failures = cf.check_dark_map({"#10283a": "$pv-ink"}, TOKENS, {"#10283a": ["essai-1"], "#eef6fa": ["essai-1"]})
    assert len(failures) == 1 and "#eef6fa" in failures[0]


def test_token_mapped_to_another_token_is_reported():
    failures = cf.check_dark_map({"#10283a": "$pv-mist"}, TOKENS, {"#10283a": ["essai-1"]})
    assert any("pv-ink" in f for f in failures)


def test_shared_light_value_may_take_either_token():
    # pv-ecume (footer text) and pv-eau (water in figures) share their light value only.
    tokens = {"pv-ecume": "#bfe3ee", "pv-eau": "#bfe3ee"}
    assert cf.check_dark_map({"#bfe3ee": "$pv-eau"}, tokens, {"#bfe3ee": ["essai-1"]}) == []
    assert cf.check_dark_map({"#bfe3ee": "$pv-mist"}, tokens, {"#bfe3ee": ["essai-1"]})


def test_colours_of_a_drawing_are_collected():
    assert cf.colours_in('<circle fill="#7F9FB3"/> var INK = "#0a5c9e";') == {"#7f9fb3", "#0a5c9e"}


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
