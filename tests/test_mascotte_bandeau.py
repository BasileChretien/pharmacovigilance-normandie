"""The mascot in the title banner (assets/filters/mascotte.lua, _includes/title-block.html).

Renders a minimal Quarto project with the site's filter and banner partial: the page's
`mascotte:` (its own, or its folder's _metadata.yml) becomes an <img> in the banner, with a
path relative to the page. Skipped where Quarto is not installed, except in CI.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from test_page_meta_filter import _run

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "assets" / "filters" / "mascotte.lua"
PARTIAL = ROOT / "_includes" / "title-block.html"

PROJET = """project:
  type: default
format:
  html:
    title-block-banner: true
    template-partials:
      - title-block.html
filters:
  - mascotte.lua
"""
PAGES = {
    "comprendre/_metadata.yml": "mascotte: comprendre\n",
    "comprendre/page.qmd": "---\ntitle: Page\n---\n\nTexte.\n",
    "comprendre/sous/page.qmd": "---\ntitle: Plus bas\n---\n\nTexte.\n",
    "comprendre/autre.qmd": "---\ntitle: Autre\nmascotte: sobre\n---\n\nTexte.\n",
    # The mascot already stands in the body: none in the banner.
    "comprendre/corps.qmd": (
        "---\ntitle: Corps\n---\n\n"
        '<img class="mascotte" src="../assets/img/mascotte/mascotte-sobre.svg" alt="">\n'
    ),
    "racine.qmd": "---\ntitle: Racine\nmascotte: sobre\n---\n\nTexte.\n",
    "inconnue.qmd": "---\ntitle: Inconnue\nmascotte: nulle-part\n---\n\nTexte.\n",
    "chemin.qmd": "---\ntitle: Chemin\nmascotte: ../../secret\n---\n\nTexte.\n",
    "sans.qmd": "---\ntitle: Sans\n---\n\nTexte.\n",
}


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> tuple[Path, str]:
    root = tmp_path_factory.mktemp("bandeau")
    shutil.copy(FILTER, root / "mascotte.lua")
    shutil.copy(PARTIAL, root / "title-block.html")
    (root / "_quarto.yml").write_text(PROJET, encoding="utf-8")
    variantes = root / "assets" / "img" / "mascotte"
    variantes.mkdir(parents=True)
    for nom in ("comprendre", "sobre"):
        (variantes / f"mascotte-{nom}.svg").write_text("<svg/>", encoding="utf-8")
    for chemin, texte in PAGES.items():
        (root / chemin).parent.mkdir(parents=True, exist_ok=True)
        (root / chemin).write_text(texte, encoding="utf-8")
    return root, _run(["render"], root)


def banniere(root: Path, page: str) -> list[str]:
    """The <img> tags of the page's title banner."""
    html = (root / page).with_suffix(".html").read_text(encoding="utf-8")
    entete = re.search(r'<header id="title-block-header".*?</header>', html, re.DOTALL)
    assert entete, page
    return re.findall(r"<img\b[^>]*>", entete.group(0))


def test_the_section_variant_reaches_its_pages_with_a_path_from_each(site):
    root, _ = site
    (tag,) = banniere(root, "comprendre/page.qmd")
    assert 'src="../assets/img/mascotte/mascotte-comprendre.svg"' in tag
    (tag,) = banniere(root, "comprendre/sous/page.qmd")
    assert 'src="../../assets/img/mascotte/mascotte-comprendre.svg"' in tag
    (tag,) = banniere(root, "racine.qmd")
    assert 'src="assets/img/mascotte/mascotte-sobre.svg"' in tag


def test_a_page_may_choose_another_variant_than_its_section(site):
    root, _ = site
    (tag,) = banniere(root, "comprendre/autre.qmd")
    assert "mascotte-sobre.svg" in tag


def test_the_banner_mascot_is_decorative(site):
    root, _ = site
    (tag,) = banniere(root, "comprendre/page.qmd")
    assert 'alt=""' in tag and 'aria-hidden="true"' in tag
    assert 'class="mascotte mascotte-titre"' in tag


def test_no_banner_mascot_where_the_body_has_one_or_none_is_chosen(site):
    root, _ = site
    assert banniere(root, "comprendre/corps.qmd") == []
    assert banniere(root, "sans.qmd") == []


def test_an_unknown_or_odd_variant_warns_and_shows_nothing(site):
    root, printed = site
    assert banniere(root, "inconnue.qmd") == []
    assert banniere(root, "chemin.qmd") == []
    assert "mascotte « nulle-part »" in printed
    assert "mascotte « ../../secret »" in printed
