"""Tests for assets/filters/tableaux.lua (every table in its own box; cards on phones for
tables of three columns or more; docs/tableaux.md), run through Quarto's Pandoc."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "assets" / "filters" / "tableaux.lua"

DEUX_COLONNES = """
| Question | Section du RCP |
|---|---|
| Pour quoi est-il autorisé ? | 4.1 Indications |
"""

TROIS_COLONNES = """
| Association | Niveau | Conduite à tenir |
|---|---|---|
| AVK + AINS | Association déconseillée | Surveiller l'INR |
| AVK + aspirine | Contre-indication | Éviter |
"""


def _quarto() -> str:
    quarto = shutil.which("quarto")
    if quarto is None:
        if os.environ.get("CI"):
            pytest.fail("Quarto is not installed: in CI, run pytest after quarto-actions/setup")
        pytest.skip("Quarto is not installed")
    return quarto


def _pandoc(tmp_path: Path, texte: str, lecteur: str = "markdown", sortie: str = "html") -> str:
    entree = tmp_path / ("page.html" if lecteur == "html" else "page.md")
    entree.write_text(texte, encoding="utf-8")
    # Written to a file: Quarto's wrapper re-encodes stdout on Windows.
    result = subprocess.run(
        [_quarto(), "pandoc", entree.name, "-f", lecteur, "-t", sortie, "--wrap=none", "-o", "out.txt"]
        + ["--lua-filter", str(FILTER)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return (tmp_path / "out.txt").read_text(encoding="utf-8")


def _boite(html: str) -> str:
    """The class attribute of the box around the (first) table."""
    found = re.search(r'<div class="(tableau-defile[^"]*)">\s*<div class="tableau-defile-cadre">\s*<table', html)
    assert found, html
    return found.group(1)


def test_a_table_of_two_columns_is_boxed_and_wraps(tmp_path):
    html = _pandoc(tmp_path, DEUX_COLONNES)
    assert _boite(html) == "tableau-defile"
    assert "data-label" not in html
    assert html.count("</div>") == 2


def test_a_table_of_three_columns_becomes_cards_labelled_by_its_headers(tmp_path):
    html = _pandoc(tmp_path, TROIS_COLONNES)
    assert _boite(html) == "tableau-defile tableau-cartes"
    labels = re.findall(r'<td data-label="([^"]*)"', html)
    assert labels == ["Association", "Niveau", "Conduite à tenir"] * 2
    # The header row stays a real header row.
    assert re.search(r"<thead>\s*<tr[^>]*>\s*<th", html)


def test_a_header_spanning_two_columns_labels_both(tmp_path):
    html = _pandoc(
        tmp_path,
        "<table><thead><tr><th>Médicament</th><th colspan=\"2\">Dose</th></tr></thead>"
        "<tbody><tr><td>Méthotrexate</td><td>≤ 20 mg</td><td>&gt; 20 mg</td></tr></tbody></table>",
        lecteur="html",
    )
    assert re.findall(r'data-label="([^"]*)"', html) == ["Médicament", "Dose", "Dose"]


def test_a_table_without_header_row_keeps_its_columns(tmp_path):
    html = _pandoc(
        tmp_path,
        "<table><tbody><tr><td>a</td><td>b</td><td>c</td></tr></tbody></table>",
        lecteur="html",
    )
    assert _boite(html) == "tableau-defile"
    assert "data-label" not in html


def test_a_grid_keeps_its_columns_and_scrolls(tmp_path):
    html = _pandoc(
        tmp_path,
        '<table class="cyp-grille tableau-large"><thead><tr><th>Médicament</th><th>CYP1A2</th>'
        "<th>CYP2D6</th></tr></thead><tbody><tr><th>Clozapine</th><td>Majeure</td><td></td></tr>"
        "</tbody></table>",
        lecteur="html",
    )
    assert _boite(html) == "tableau-defile tableau-large"
    assert "data-label" not in html


def test_a_table_whose_generator_wrote_the_box_is_left_alone(tmp_path):
    html = _pandoc(
        tmp_path,
        '<table class="tableau-encadre"><thead><tr><th>a</th><th>b</th><th>c</th></tr></thead>'
        "<tbody><tr><td>1</td><td>2</td><td>3</td></tr></tbody></table>",
        lecteur="html",
    )
    assert "tableau-defile" not in html and "data-label" not in html


def test_other_formats_are_left_alone(tmp_path):
    assert "tableau-defile" not in _pandoc(tmp_path, TROIS_COLONNES, sortie="markdown")
