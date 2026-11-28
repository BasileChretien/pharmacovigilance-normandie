"""The mascot (docs/mascotte/README.md): where it may appear, and how.

A Norman with a pill shield, sounding the horn. Decorative, placed as an <img> (its own
colours and white edge read in both themes and under Dark Reader), and kept off medicine,
class, pregnancy, alert and serious-harm pages.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "checks"))

from check_contrast import parse_scss_tokens
from check_figures import check_svg

MASCOTTE = ROOT / "assets" / "img" / "mascotte.svg"
RECHERCHE = ROOT / "_includes" / "mascotte-recherche.html"
THEME = ROOT / "assets" / "theme.scss"

# The pages that show the mascot, and only these: a new place is a decision taken here.
# Each takes the variant of its context (tools/design/make_mascotte.py).
PAGES = {
    "index.qmd": "mascotte-accueil",  # small, beside "Déclarer": sounds the alert
    "404.qmd": "mascotte-404",  # lost
    "vigiking/index.qmd": "mascotte-vigiking",  # the bulletin's masthead: announces
    "vigiking/archives.qmd": "mascotte-vigiking",
    "crpv/recherche.qmd": "mascotte-attente",  # the publications list, while it is empty
}
# Shown only by an empty state that may be filled later.
PAGES_PARFOIS = {"crpv/recherche.qmd"}
# Never there: medicine and class sheets, pregnancy, safety alerts, serious harm.
INTERDITS = (
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


def with_includes(page: Path) -> str:
    """The page's source followed by the files it includes."""
    text = page.read_text(encoding="utf-8")
    for name in _INCLUDE.findall(text):
        included = (page.parent / name).resolve()
        if included.exists():
            text += "\n" + included.read_text(encoding="utf-8")
    return text


def pages_with_mascot() -> dict[str, str]:
    found = {}
    for page in site_pages():
        text = with_includes(page)
        if re.search(_SVG, text):
            found[page.relative_to(ROOT).as_posix()] = text
    return found


def test_the_mascot_is_on_the_chosen_pages_and_nowhere_else():
    found = set(pages_with_mascot())
    assert found <= set(PAGES), (
        f"mascotte sur une page non prévue : {sorted(found - set(PAGES))}"
    )
    missing = set(PAGES) - PAGES_PARFOIS - found
    assert not missing, f"mascotte absente de : {sorted(missing)}"


def test_each_page_shows_the_variant_of_its_context():
    for page, text in pages_with_mascot().items():
        noms = set(re.findall(r"(mascotte(?:-[\w-]+)?)\.svg", text))
        assert noms == {PAGES[page]}, f"{page} : {sorted(noms)}"
    assert "mascotte/mascotte-recherche.svg" in RECHERCHE.read_text(encoding="utf-8")


def test_no_chosen_page_is_a_medicine_alert_or_serious_harm_page():
    assert not [p for p in PAGES if p.startswith(INTERDITS)]


def test_every_mascot_is_decorative():
    for page, text in pages_with_mascot().items():
        for tag in _IMG_HTML.findall(text):
            assert 'alt=""' in tag and 'aria-hidden="true"' in tag, f"{page} : {tag}"
        # Pandoc drops an empty alt from a Markdown image: the mascot is an <img> tag.
        assert not _IMG_MD.search(text), (
            f'{page} : image Markdown, écrire <img … alt="">'
        )


def test_the_search_empty_state_keeps_the_mascot_off_forbidden_pages():
    script = RECHERCHE.read_text(encoding="utf-8")
    for area in (
        "medicaments",
        "actualites",
        "cas-marquants",
        "que-faire-effet-indesirable",
    ):
        assert area in script, (
            f"{area} manque aux zones sans mascotte de {RECHERCHE.name}"
        )
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
