"""The mascot (docs/mascotte/README.md): where it appears, and how.

A Norman with a pill shield, sounding the horn. Decorative, placed as an <img> (its own
colours and white edge read in both themes and under Dark Reader). Every page shows it: in
its title banner, in the variant of its section (`mascotte:` in the section's
_metadata.yml, or in the page's front matter, put there by assets/filters/mascotte.lua and
_includes/title-block.html), or in its body for the pages of PAGES. Pages about risks,
dosages and serious harm get a gentle variant (make_mascotte.DOUX).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import make_mascotte as mm
import pytest
import yaml
from check_contrast import parse_scss_tokens
from check_figures import check_svg

ROOT = Path(__file__).resolve().parents[1]
MASCOTTE = ROOT / "assets" / "img" / "mascotte.svg"
RECHERCHE = ROOT / "_includes" / "mascotte-recherche.html"
PARTIAL = ROOT / "_includes" / "title-block.html"
THEME = ROOT / "assets" / "theme.scss"

# The pages that show the mascot in their body, and only these: a new place is a decision
# taken here. Each takes the variant of its context (tools/design/make_mascotte.py); the
# filter then leaves their banner without one.
PAGES = {
    "index.qmd": "mascotte-accueil",  # small, beside "Déclarer": sounds the alert
    "404.qmd": "mascotte-404",  # lost
    "vigiking/index.qmd": "mascotte-vigiking",  # the bulletin's masthead: announces
    "vigiking/archives.qmd": "mascotte-vigiking",
    "crpv/recherche.qmd": "mascotte-attente",  # the publications list, while it is empty
}
# Shown only by an empty state that may be filled later.
PAGES_PARFOIS = {"crpv/recherche.qmd"}
# Medicine and class sheets, pregnancy, safety alerts, serious harm: a gentle variant.
SERIEUX = (
    "medicaments/",
    "actualites/",
    "normandie/cas-marquants.qmd",
    "que-faire-effet-indesirable.qmd",
)

_INCLUDE = re.compile(r"\{\{<\s*include\s+(\S+)\s*>\}\}")
_SVG = r"mascotte(?:-[\w-]+)?\.svg"
_IMG_HTML = re.compile(r"<img\b[^>]*" + _SVG + r"[^>]*>")
_IMG_MD = re.compile(r"!\[([^\]]*)\]\([^)]*" + _SVG + r"\)(\{[^}]*\})?")
_MOTION_OK = re.compile(r"@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{")
_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def site_pages() -> list[Path]:
    """The pages Quarto renders (folders starting with _ or . are not pages)."""
    return [
        p
        for p in ROOT.rglob("*.qmd")
        if not any(
            part.startswith(("_", ".")) for part in p.relative_to(ROOT).parts[:-1]
        )
        and p.relative_to(ROOT).parts[0]
        not in {"docs", "tests", "tools", "node_modules"}
    ]


def rel(page: Path) -> str:
    return page.relative_to(ROOT).as_posix()


def with_includes(page: Path) -> str:
    """The page's source followed by the files it includes."""
    text = page.read_text(encoding="utf-8")
    for name in _INCLUDE.findall(text):
        included = (page.parent / name).resolve()
        if included.exists():
            text += "\n" + included.read_text(encoding="utf-8")
    return text


def pages_with_mascot() -> dict[str, str]:
    """The pages with a mascot in their body."""
    found = {}
    for page in site_pages():
        text = with_includes(page)
        if re.search(_SVG, text):
            found[rel(page)] = text
    return found


def front_matter(page: Path) -> dict:
    match = _FRONT.match(page.read_text(encoding="utf-8"))
    return (yaml.safe_load(match.group(1)) or {}) if match else {}


def contexte_bandeau(page: Path) -> str | None:
    """The banner's variant, as Quarto merges it: the page's front matter, else the
    nearest _metadata.yml of its folders."""
    if "mascotte" in (fm := front_matter(page)):
        return fm["mascotte"]
    for folder in page.parents:
        if folder == ROOT.parent:
            break
        meta = folder / "_metadata.yml"
        if meta.exists():
            data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
            if "mascotte" in data:
                return data["mascotte"]
    return None


def sections() -> set[str]:
    return {p.relative_to(ROOT).parts[0] for p in site_pages() if p.parent != ROOT}


def test_the_mascot_is_in_the_body_of_the_chosen_pages_only():
    found = set(pages_with_mascot())
    assert found <= set(PAGES), (
        f"mascotte dans le corps d'une page non prévue : {sorted(found - set(PAGES))}"
    )
    missing = set(PAGES) - PAGES_PARFOIS - found
    assert not missing, f"mascotte absente de : {sorted(missing)}"


def test_each_page_shows_the_variant_of_its_context():
    for page, text in pages_with_mascot().items():
        noms = set(re.findall(r"(mascotte(?:-[\w-]+)?)\.svg", text))
        assert noms == {PAGES[page]}, f"{page} : {sorted(noms)}"
    assert "mascotte/mascotte-recherche.svg" in RECHERCHE.read_text(encoding="utf-8")


def test_every_page_shows_the_mascot():
    """In its body (PAGES), or in its title banner in a variant that exists."""
    sans = []
    for page in site_pages():
        if rel(page) in PAGES:
            continue
        contexte = contexte_bandeau(page)
        if contexte is None:
            sans.append(rel(page))
        else:
            assert contexte in mm.CONTEXTES, (
                f"{rel(page)} : mascotte « {contexte} » inconnue"
            )
    assert not sans, f"pages sans mascotte : {sorted(sans)}"


def test_each_section_has_a_variant_of_its_own():
    choix = {}
    for section in sorted(sections()):
        meta = ROOT / section / "_metadata.yml"
        assert meta.exists(), f"{section}/_metadata.yml manque (clé mascotte:)"
        choix[section] = yaml.safe_load(meta.read_text(encoding="utf-8"))["mascotte"]
    assert len(set(choix.values())) == len(choix), choix


def test_pages_about_risks_get_a_gentle_variant():
    for page in site_pages():
        if rel(page).startswith(SERIEUX) and rel(page) not in PAGES:
            contexte = contexte_bandeau(page)
            assert contexte in mm.DOUX, f"{rel(page)} : « {contexte} »"


def test_every_mascot_is_decorative():
    texts = dict(pages_with_mascot())
    texts[PARTIAL.name] = PARTIAL.read_text(encoding="utf-8")
    for page, text in texts.items():
        for tag in re.findall(r"<img\b[^>]*mascotte[^>]*>", text):
            assert 'alt=""' in tag and 'aria-hidden="true"' in tag, f"{page} : {tag}"
        # Pandoc drops an empty alt from a Markdown image: the mascot is an <img> tag.
        assert not _IMG_MD.search(text), (
            f'{page} : image Markdown, écrire <img … alt="">'
        )
    assert _IMG_HTML.search(texts["index.qmd"])


def _quarto_banner_partial() -> Path:
    quarto = shutil.which("quarto")
    if quarto is None:
        pytest.skip("Quarto is not installed")
    for base in (Path(quarto).resolve().parents[1], Path(quarto).parents[1]):
        partial = base / "share/formats/html/templates/banner/title-block.html"
        if partial.exists():
            return partial
    pytest.skip("Quarto's banner partial was not found")


def test_the_banner_partial_is_quartos_with_the_mascot_added():
    """A Quarto upgrade that changes its banner fails here: copy its partial again and put
    the mascot's lines back."""
    quarto = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
    assert re.search(
        r"template-partials:\s*\n\s*-\s*_includes/title-block\.html", quarto
    )
    ours = PARTIAL.read_text(encoding="utf-8").splitlines()
    sans_mascotte = [
        line for line in ours if "mascotte" not in line and not line.startswith("$--")
    ]
    theirs = _quarto_banner_partial().read_text(encoding="utf-8").splitlines()
    assert sans_mascotte == theirs


def test_the_search_empty_state_shows_the_mascot_on_every_page():
    script = RECHERCHE.read_text(encoding="utf-8")
    assert "location.pathname" not in script
    quarto = (ROOT / "_quarto.yml").read_text(encoding="utf-8")
    assert "_includes/mascotte-recherche.html" in quarto


def test_the_drawing_uses_only_the_theme_tokens_and_the_figure_rules():
    tokens = parse_scss_tokens(THEME.read_text(encoding="utf-8"))
    assert check_svg("mascotte", MASCOTTE.read_text(encoding="utf-8"), tokens) == []


def _without_motion_blocks(scss: str) -> str:
    """theme.scss without its @media (prefers-reduced-motion: no-preference) blocks."""
    out, pos = [], 0
    for match in _MOTION_OK.finditer(scss):
        if match.start() < pos:
            continue
        out.append(scss[pos : match.start()])
        depth, i = 1, match.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(scss[i], 0)
            i += 1
        pos = i
    out.append(scss[pos:])
    return "".join(out)


def test_the_mascot_moves_only_when_motion_is_not_reduced():
    scss = THEME.read_text(encoding="utf-8")
    assert "mascotte" in scss
    rest = _without_motion_blocks(scss)
    for selector, body in re.findall(r"([^{};]*mascotte[^{};]*)\{([^{}]*)\}", rest):
        assert not re.search(r"\b(transition|animation)\s*:", body), selector.strip()
