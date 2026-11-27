"""Tests for assets/filters/page-meta.lua, run through the pandoc that Quarto bundles.

Skipped where Quarto is not installed (the CI job runs pytest before installing it).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "assets" / "filters" / "page-meta.lua"
QUARTO = shutil.which("quarto")

pytestmark = pytest.mark.skipif(QUARTO is None, reason="Quarto is not installed")

PAGE = "---\ntitle: Fiche\nsubstances: [ibuprofène]\n---\n\nTexte.\n"
DONNEES = {
    "source": "BDPM",
    "mis_a_jour": "2026-11-20",
    "substances": {
        "ibuprofène": {
            "cis": "68634000",
            "nom": "ADVIL 200 mg, comprimé enrobé",
            "princeps": True,
            "association": False,
            "nb": 1,
        }
    },
    "pages": {},
    "cites": {},
}


def _render(tmp_path: Path, donnees: dict) -> tuple[str, str]:
    """The page's HTML and what the filter printed on stderr."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "bdpm-liens.json").write_text(
        json.dumps(donnees, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "fiche.md").write_text(PAGE, encoding="utf-8")
    # Written to a file: Quarto's wrapper re-encodes stdout on Windows.
    result = subprocess.run(
        [QUARTO, "pandoc", "fiche.md", "-t", "html", "--wrap=none", "-o", "out.html"]
        + ["--lua-filter", str(FILTER)],
        cwd=tmp_path,
        check=False,  # the return code is asserted below, with stderr shown
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return (tmp_path / "out.html").read_text(encoding="utf-8"), result.stderr


def test_a_page_missing_from_the_pages_read_warns_and_keeps_the_site_wide_example(
    tmp_path,
):
    # Outside a Quarto project the page's path is unknown, so it matches no page read.
    html, stderr = _render(
        tmp_path, {**DONNEES, "pages_lues": ["medicaments/fiche.qmd"]}
    )
    assert "ADVIL 200 mg" in html
    assert "bdpm-liens.json" in stderr


def test_data_without_the_list_of_pages_read_gives_no_warning(tmp_path):
    html, stderr = _render(tmp_path, DONNEES)
    assert "ADVIL 200 mg" in html
    assert "bdpm-liens.json" not in stderr
