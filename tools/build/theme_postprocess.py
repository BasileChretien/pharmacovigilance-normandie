"""Make the HTML of Quarto's light/dark switch valid, without changing what it does.

Quarto 1.10 writes each theme stylesheet three times (light, dark, and a spare light copy)
under the same id, which html-validate rejects (no-dup-id), and its switch is a link with
no text. After each render, this script:

- removes the spare light copies (class quarto-color-scheme-extra) and the two lines of
  Quarto's script that disable them as the page loads: with a light default, nothing else
  uses them;
- gives the dark stylesheets their own ids (-sombre), and points the one line of Quarto's
  script that looks for the dark stylesheet at the new id;
- gives the switch the role and the name of a button (_includes/theme-sombre.html then
  keeps aria-pressed in step with the theme).

If Quarto writes something else (an upgrade), the script stops the build rather than
patch half a page: compare with tests/test_theme_postprocess.py and adapt.

Run by Quarto as a post-render script (see _quarto.yml), or by hand:
    python tools/build/theme_postprocess.py [file.html ...]
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SUFFIX = "-sombre"
IDS = ("quarto-bootstrap", "quarto-text-highlighting-styles")
_EXTRA_LINK = re.compile(r'[ \t]*<link [^>]*class="quarto-color-scheme-extra"[^>]*>\r?\n?')
_DARK_ID = re.compile(r'(<link [^>]*class="quarto-color-scheme quarto-color-alternate"[^>]*\bid=")([\w-]+)(")')
_EXTRA_LINE = re.compile(
    r"[ \t]*document\.querySelector\('link#(?:quarto-bootstrap|quarto-text-highlighting-styles)"
    r"\.quarto-color-scheme-extra'\)\.rel = 'disabled-stylesheet';\r?\n"
)
DARK_TEST = 'if (sheetNode.id === "quarto-bootstrap") {'
TOGGLE = '<a href="" class="quarto-color-scheme-toggle'
TOGGLE_BUTTON = '<a href="" role="button" aria-label="Thème sombre" class="quarto-color-scheme-toggle'


def _expect(count: int, wanted: int, what: str) -> None:
    if count != wanted:
        raise ValueError(f"{what} : {count} trouvé(s), {wanted} attendu(s) (balisage de Quarto changé ?)")


def _rename_dark(match: re.Match[str]) -> str:
    if match.group(2) not in IDS:
        raise ValueError(f"feuille sombre d'id inattendu « {match.group(2)} »")
    return match.group(1) + match.group(2) + SUFFIX + match.group(3)


def patch(html: str) -> str:
    """The page with valid markup for the switch; unchanged if it has none or is done."""
    if "quarto-color-scheme" not in html or f'"quarto-bootstrap{SUFFIX}"' in html:
        return html
    html, links = _EXTRA_LINK.subn("", html)
    _expect(links, len(IDS), "feuilles de style « extra »")
    html, lines = _EXTRA_LINE.subn("", html)
    _expect(lines, len(IDS), "lignes du script qui désactivent les feuilles « extra »")
    html, dark = _DARK_ID.subn(_rename_dark, html)
    _expect(dark, len(IDS), "feuilles de style sombres")
    _expect(html.count(DARK_TEST), 1, "test sheetNode.id du script de Quarto")
    html = html.replace(DARK_TEST, DARK_TEST.replace('"quarto-bootstrap"', f'"quarto-bootstrap{SUFFIX}"'))
    if TOGGLE not in html:
        raise ValueError("bouton de thème (quarto-color-scheme-toggle) introuvable")
    return html.replace(TOGGLE, TOGGLE_BUTTON)


def output_files(argv: list[str]) -> list[Path]:
    if argv:
        return [Path(a) for a in argv]
    listed = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "")
    if listed.strip():
        return [Path(f) for f in listed.splitlines() if f.strip().endswith(".html")]
    return sorted(Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site")).rglob("*.html"))


def main(argv: list[str]) -> int:
    changed = 0
    for path in output_files(argv):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        try:
            new = patch(text)
        except ValueError as error:
            print(f"theme_postprocess : {path} : {error}", file=sys.stderr)
            return 1
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(f"theme_postprocess : {changed} page(s) corrigée(s) (thèmes clair et sombre).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
