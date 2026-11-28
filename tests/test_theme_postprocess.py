"""Tests for tools/build/theme_postprocess.py (valid HTML for Quarto's light/dark switch)."""

import re

import pytest
import theme_postprocess as tp

# The parts of a page that Quarto 1.10 writes for its light/dark switch (_site, 28/11/2026).
PAGE = """<head>
<link href="../site_libs/quarto-html/quarto-syntax-highlighting-bb8a.css" rel="stylesheet" class="quarto-color-scheme" id="quarto-text-highlighting-styles">
<link href="../site_libs/quarto-html/quarto-syntax-highlighting-dark-665d.css" rel="stylesheet" class="quarto-color-scheme quarto-color-alternate" id="quarto-text-highlighting-styles">
<link href="../site_libs/quarto-html/quarto-syntax-highlighting-bb8a.css" rel="stylesheet" class="quarto-color-scheme-extra" id="quarto-text-highlighting-styles">
<script src="../site_libs/bootstrap/bootstrap.min.js"></script>
<link href="../site_libs/bootstrap/bootstrap-icons.css" rel="stylesheet">
<link href="../site_libs/bootstrap/bootstrap-4676.min.css" rel="stylesheet" append-hash="true" class="quarto-color-scheme" id="quarto-bootstrap" data-mode="light">
<link href="../site_libs/bootstrap/bootstrap-dark-f029.min.css" rel="stylesheet" append-hash="true" class="quarto-color-scheme quarto-color-alternate" id="quarto-bootstrap" data-mode="dark">
<link href="../site_libs/bootstrap/bootstrap-4676.min.css" rel="stylesheet" append-hash="true" class="quarto-color-scheme-extra" id="quarto-bootstrap" data-mode="light">
</head>
<body>
<script id = "quarto-html-before-body" type="application/javascript">
    const toggleBodyColorPrimary = () => {
      const bsSheetEl = window.document.querySelector("link#quarto-bootstrap:not([rel=disabled-stylesheet])");
    }
        for (const sheetNode of alternateStylesheets) {
          if (sheetNode.id === "quarto-bootstrap") {
            toggleBodyColorMode(sheetNode);
          }
        }
      document.querySelector('link#quarto-text-highlighting-styles.quarto-color-scheme-extra').rel = 'disabled-stylesheet';
      document.querySelector('link#quarto-bootstrap.quarto-color-scheme-extra').rel = 'disabled-stylesheet';
    let localAlternateSentinel = darkModeDefault ? 'alternate' : 'default';
</script>
<a href="" class="quarto-color-scheme-toggle quarto-navigation-tool  px-1" onclick="window.quartoToggleColorScheme(); return false;" title="Basculer le mode sombre"><i class="bi"></i></a>
</body>"""


def test_ids_become_unique():
    ids = re.findall(r'\bid="([^"]+)"', tp.patch(PAGE))
    assert len(ids) == len(set(ids))
    assert "quarto-bootstrap-sombre" in ids and "quarto-text-highlighting-styles-sombre" in ids


def test_the_light_stylesheet_keeps_quartos_id():
    out = tp.patch(PAGE)
    assert 'class="quarto-color-scheme" id="quarto-bootstrap" data-mode="light"' in out
    assert 'link#quarto-bootstrap:not([rel=disabled-stylesheet])' in out


def test_quartos_switch_finds_the_dark_stylesheet_by_its_new_id():
    out = tp.patch(PAGE)
    assert 'if (sheetNode.id === "quarto-bootstrap-sombre") {' in out
    assert 'id="quarto-bootstrap-sombre" data-mode="dark"' in out


def test_the_spare_light_stylesheets_and_their_lines_go():
    # Quarto disables them as the page loads when the author's default is light.
    out = tp.patch(PAGE)
    assert "quarto-color-scheme-extra" not in out
    assert "let localAlternateSentinel" in out


def test_the_switch_is_a_named_button_in_the_html():
    out = tp.patch(PAGE)
    assert '<a href="" role="button" aria-label="Thème sombre" class="quarto-color-scheme-toggle' in out


def test_patching_twice_changes_nothing_more():
    once = tp.patch(PAGE)
    assert tp.patch(once) == once


def test_a_page_without_the_switch_is_left_alone():
    page = '<head><link href="style.css" rel="stylesheet"></head><body></body>'
    assert tp.patch(page) == page


def test_unexpected_quarto_markup_stops_the_build():
    # A Quarto upgrade that changes the switch must be noticed, not half-patched.
    with pytest.raises(ValueError, match="sheetNode"):
        tp.patch(PAGE.replace('if (sheetNode.id === "quarto-bootstrap") {', 'if (isBootstrap(sheetNode)) {'))
    with pytest.raises(ValueError, match="extra"):
        tp.patch(PAGE.replace(' class="quarto-color-scheme-extra" id="quarto-bootstrap"', ' class="quarto-color-scheme" id="x"'))
