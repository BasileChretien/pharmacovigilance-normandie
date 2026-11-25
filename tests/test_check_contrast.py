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
