"""Tests for tools/checks/check_contrast.py (WCAG contrast of the design tokens)."""

import check_contrast as ck
import pytest


def test_black_on_white_is_21():
    assert ck.contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, rel=1e-3)


def test_same_colour_is_1():
    assert ck.contrast_ratio("#1b4f8a", "#1b4f8a") == pytest.approx(1.0)


def test_scss_variables_are_parsed():
    scss = "$pv-ink: #1f2328;   // texte\n$primary: $pv-ink;\n$pv-paper: #FFFFFF;"
    tokens = ck.parse_scss_tokens(scss)
    assert tokens["pv-ink"] == "#1f2328"
    assert tokens["pv-paper"] == "#ffffff"
    assert "primary" not in tokens


def test_failing_pair_is_reported():
    tokens = {"gris": "#777777", "blanc": "#ffffff"}
    pairs = [{"texte": "gris", "fond": "blanc", "minimum": 4.5, "usage": "texte courant"}]
    failures = ck.check_pairs(tokens, pairs)
    assert len(failures) == 1


def test_unknown_token_is_reported():
    failures = ck.check_pairs({"blanc": "#ffffff"}, [{"texte": "absent", "fond": "blanc", "minimum": 4.5}])
    assert "absent" in failures[0]


def test_site_theme_passes(capsys):
    assert ck.main() == 0
    assert "paires conformes" in capsys.readouterr().out


def test_default_flag_is_parsed():
    # The light tokens carry !default so that the dark theme file can override them.
    tokens = ck.parse_scss_tokens("$pv-ink: #10283a !default;   // texte\n$pv-paper: #ffffff  !default ;")
    assert tokens == {"pv-ink": "#10283a", "pv-paper": "#ffffff"}


def test_dark_tokens_override_light_ones():
    themes = ck.theme_tokens("$a: #000000 !default;\n$b: #ffffff !default;", "$a: #eeeeee;")
    assert themes["clair"] == {"a": "#000000", "b": "#ffffff"}
    assert themes["sombre"] == {"a": "#eeeeee", "b": "#ffffff"}


def test_each_pair_is_checked_in_both_themes():
    themes = {"clair": {"t": "#000000", "f": "#ffffff"}, "sombre": {"t": "#333333", "f": "#000000"}}
    failures = ck.check_themes(themes, [{"texte": "t", "fond": "f", "minimum": 4.5, "usage": "x"}])
    assert len(failures) == 1
    assert "sombre" in failures[0]


def test_a_pair_can_be_limited_to_one_theme():
    themes = {"clair": {"t": "#000000", "f": "#ffffff"}, "sombre": {"t": "#333333", "f": "#000000"}}
    pair = {"texte": "t", "fond": "f", "minimum": 4.5, "themes": ["clair"]}
    assert ck.check_themes(themes, [pair]) == []


def test_unknown_theme_name_is_reported():
    themes = {"clair": {"t": "#000000", "f": "#ffffff"}, "sombre": {"t": "#000000", "f": "#ffffff"}}
    failures = ck.check_themes(themes, [{"texte": "t", "fond": "f", "themes": ["nuit"]}])
    assert "nuit" in failures[0]


def test_dark_token_the_check_cannot_read_is_reported():
    # Otherwise the pair would be checked on the light value and pass (review of #43).
    light = "$pv-ink: #10283a !default;\n$pv-paper: #ffffff !default;"
    dark = "$pv-ink: #fff;\n$pv-paper: lighten($pv-ink, 10%);\n$pv-figures-sombre: (\n);"
    assert ck.unread_dark_tokens(light, dark) == ["pv-ink", "pv-paper"]
    assert ck.unread_dark_tokens(light, "$pv-ink: #e3ecf2;") == []
