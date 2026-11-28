"""Tests for the annotated SmPC of comprendre/lire-un-rcp.qmd: its filter
(assets/filters/rcp-annote.lua, run through Quarto) and the page's sections."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "assets" / "filters" / "rcp-annote.lua"
PAGE = ROOT / "comprendre" / "lire-un-rcp.qmd"

SECTION = """::: {.rcp-annote}

::: {.rcp-section numero="4.8" titre="Effets <indésirables> & co"}
**À y chercher.** Les effets.

**Dans ce RCP.** Une liste.
:::

:::
"""


def _quarto() -> str:
    quarto = shutil.which("quarto")
    if quarto is None:
        if os.environ.get("CI"):
            pytest.fail(
                "Quarto is not installed: in CI, run pytest after quarto-actions/setup"
            )
        pytest.skip("Quarto is not installed")
    return quarto


def _pandoc(tmp_path: Path, texte: str) -> subprocess.CompletedProcess:
    (tmp_path / "page.md").write_text(texte, encoding="utf-8")
    # Written to a file: Quarto's wrapper re-encodes stdout on Windows.
    return subprocess.run(
        [_quarto(), "pandoc", "page.md", "-t", "html", "--wrap=none", "-o", "out.html"]
        + ["--lua-filter", str(FILTER)],
        cwd=tmp_path,
        check=False,  # asserted by each test
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


def test_a_section_becomes_a_disclosure_with_its_number_and_title(tmp_path):
    result = _pandoc(tmp_path, SECTION)
    assert result.returncode == 0, result.stdout + result.stderr
    html = (tmp_path / "out.html").read_text(encoding="utf-8")
    assert '<details class="rcp-section">' in html
    assert (
        '<summary><span class="rcp-ligne"><span class="rcp-numero">4.8</span> '
        '<span class="rcp-titre">Effets &lt;indésirables&gt; &amp; co</span></span></summary>'
    ) in html
    note = html.split('<div class="rcp-note">', 1)[1].split("</details>", 1)[0]
    assert (
        "<strong>À y chercher.</strong>" in note
        and "<strong>Dans ce RCP.</strong>" in note
    )


def test_a_section_without_its_number_or_title_stops_the_render(tmp_path):
    result = _pandoc(tmp_path, SECTION.replace(' numero="4.8"', ""))
    assert result.returncode != 0
    assert "rcp-section" in result.stdout + result.stderr


def _sections() -> list[tuple[str, str, str]]:
    texte = PAGE.read_text(encoding="utf-8")
    return re.findall(
        r'::: \{\.rcp-section numero="([^"]+)" titre="([^"]+)"\}\n(.*?)\n:::\n',
        texte,
        re.DOTALL,
    )


def _cle(numero: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"[0-9]+", numero.split(" ")[0]))


def test_the_page_sections_follow_the_smpc_order_and_each_has_both_notes():
    sections = _sections()
    assert len(sections) >= 15, "the annotated SmPC is expected on the page"
    # Numbered sections in order, then what the SmPC prints without a number (the
    # delivery conditions), marked "—".
    numeros = [numero for numero, _, _ in sections]
    sans_numero = [i for i, numero in enumerate(numeros) if numero == "—"]
    assert sans_numero == list(range(len(numeros) - len(sans_numero), len(numeros))), (
        numeros
    )
    cles = [_cle(numero) for numero in numeros if numero != "—"]
    assert cles == sorted(cles), numeros
    # Short numbers: they fit the first column of each line (theme.scss, .rcp-ligne).
    assert all(len(numero) <= 5 for numero, _, _ in sections)
    for numero, _, note in sections:
        assert note.startswith("**À y chercher.** "), numero
        assert "\n\n**Dans ce RCP.** " in note, numero


def test_the_page_cites_the_smpc_it_annotates():
    texte = PAGE.read_text(encoding="utf-8")
    assert (
        "base-donnees-publique.medicaments.gouv.fr/medicament/68634000/extrait" in texte
    )


def test_the_plan_runs_to_the_end_of_the_smpc():
    numeros = [numero for numero, _, _ in _sections()]
    titres = [titre for _, titre, _ in _sections()]
    assert numeros[-2:] == ["11-12", "—"], numeros
    assert titres[-1].startswith("Conditions de prescription et de délivrance")
