"""Tests for assets/filters/page-meta.lua, run through Quarto.

Two ways: plain `quarto pandoc` on a file outside any project (the page's path is then
unknown), and `quarto render` of a minimal project, where the filter knows the page's path
as make_bdpm_liens.py writes it. Skipped where Quarto is not installed, except in CI, where
the job installs Quarto before running pytest: a skip there would hide the tests.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "assets" / "filters" / "page-meta.lua"

PAGE = "---\ntitle: Fiche\nsubstances: [ibuprofène]\n---\n\nTexte.\n"
ADVIL = {
    "cis": "68634000",
    "nom": "ADVIL 200 mg, comprimé enrobé",
    "princeps": True,
    "association": False,
    "nb": 1,
}
ARROW = {
    "cis": "60000001",
    "nom": "IBUPROFENE ARROW 200 mg, comprimé pelliculé",
    "princeps": False,
    "association": False,
}
DONNEES = {
    "source": "BDPM",
    "mis_a_jour": "2026-11-20",
    "substances": {"ibuprofène": ADVIL},
    "pages": {},
    "cites": {},
}


def _quarto() -> str:
    quarto = shutil.which("quarto")
    if quarto is None:
        if os.environ.get("CI"):
            pytest.fail(
                "Quarto is not installed: in CI, run pytest after quarto-actions/setup"
            )
        pytest.skip("Quarto is not installed")
    return quarto


def _run(args: list[str], cwd: Path) -> str:
    """What Quarto printed (its warnings), after checking it succeeded."""
    result = subprocess.run(
        [_quarto(), *args],
        cwd=cwd,
        check=False,  # the return code is asserted below, with the output shown
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    printed = result.stdout + result.stderr
    assert result.returncode == 0, printed
    return printed


def _data(root: Path, donnees: dict) -> None:
    (root / "data").mkdir()
    (root / "data" / "bdpm-liens.json").write_text(
        json.dumps(donnees, ensure_ascii=False), encoding="utf-8"
    )


def _render(tmp_path: Path, donnees: dict) -> tuple[str, str]:
    """A page outside any project: its HTML and what the filter printed."""
    _data(tmp_path, donnees)
    (tmp_path / "fiche.md").write_text(PAGE, encoding="utf-8")
    # Written to a file: Quarto's wrapper re-encodes stdout on Windows.
    printed = _run(
        ["pandoc", "fiche.md", "-t", "html", "--wrap=none", "-o", "out.html"]
        + ["--lua-filter", str(FILTER)],
        tmp_path,
    )
    return (tmp_path / "out.html").read_text(encoding="utf-8"), printed


def _render_project(tmp_path: Path, donnees: dict) -> tuple[str, str]:
    """medicaments/fiche.qmd in a minimal Quarto project: its HTML and what was printed."""
    _data(tmp_path, donnees)
    shutil.copy(FILTER, tmp_path / "page-meta.lua")
    (tmp_path / "_quarto.yml").write_text(
        "project:\n  type: default\nformat: html\nfilters:\n  - page-meta.lua\n",
        encoding="utf-8",
    )
    (tmp_path / "medicaments").mkdir()
    (tmp_path / "medicaments" / "fiche.qmd").write_text(PAGE, encoding="utf-8")
    printed = _run(["render"], tmp_path)
    html = (tmp_path / "medicaments" / "fiche.html").read_text(encoding="utf-8")
    return html, printed


def test_a_page_missing_from_the_pages_read_warns_and_keeps_the_site_wide_example(
    tmp_path,
):
    # Outside a Quarto project the page's path is unknown, so it matches no page read.
    html, printed = _render(
        tmp_path, {**DONNEES, "pages_lues": ["medicaments/fiche.qmd"]}
    )
    assert "ADVIL 200 mg" in html
    assert "bdpm-liens.json" in printed


def test_data_without_the_list_of_pages_read_gives_no_warning(tmp_path):
    html, printed = _render(tmp_path, DONNEES)
    assert "ADVIL 200 mg" in html
    assert "bdpm-liens.json" not in printed


def test_a_page_read_by_the_script_gets_its_own_example_without_a_warning(tmp_path):
    # The key the script writes ("medicaments/fiche.qmd") must be the path the filter
    # computes: a leading "./" or a backslash on either side would fail here.
    html, printed = _render_project(
        tmp_path,
        {
            **DONNEES,
            "pages": {"medicaments/fiche.qmd": {"ibuprofène": ARROW}},
            "pages_lues": ["medicaments/fiche.qmd"],
        },
    )
    assert "IBUPROFENE ARROW 200 mg" in html
    assert "ADVIL 200 mg" not in html
    assert "bdpm-liens.json" not in printed


def test_a_project_page_missing_from_the_pages_read_is_named_in_the_warning(tmp_path):
    html, printed = _render_project(
        tmp_path, {**DONNEES, "pages_lues": ["medicaments/autre.qmd"]}
    )
    assert "ADVIL 200 mg" in html
    # Quoted as the warning writes it (Quarto's progress line names the file too).
    assert "« medicaments/fiche.qmd » absente de data/bdpm-liens.json" in printed
