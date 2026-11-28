"""Put the prototype notice and the skip link where they belong around the fixed header.

After each render, this script changes two things in every page, without changing what
they say:

- the prototype notice (website.announcement in _quarto.yml) leaves the header. Quarto
  writes it as the last child of <header id="quarto-header">, which is fixed to the top of
  the screen: on a 390 x 844 phone the header and the notice covered 197 px, 30 % of the
  screen, each time the reader scrolled back up. Moved just after the header, the notice
  opens every page, then scrolls away with the text; only the navigation bar comes back.
  Quarto's script finds it by its id wherever it is, and sizes the page's top margin from
  the header alone. Out of the header, it is named as a region ("Avertissement"), so that
  all of the page stays inside landmarks. It also loses Quarto's class "hidden", which its
  script lifts once the page has loaded: the text then jumped down by the notice's height
  on every page, and a reader without JavaScript never saw the warning (it cannot be
  dismissed: dismissable: false);
- the skip link ("Aller au contenu", include-before-body in _quarto.yml) comes first.
  Quarto writes it at the top of the content, after the ten links of the navigation it
  is meant to skip.

If Quarto writes something else (an upgrade), the script stops the build rather than patch
half a page: compare with tests/test_entete_postprocess.py and adapt.

Run by Quarto as a post-render script (see _quarto.yml), or by hand:
    python tools/build/entete_postprocess.py [file.html ...]
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HEADER = '<header id="quarto-header"'
NOTICE = '<div id="quarto-announcement"'
LABEL = ' role="region" aria-label="Avertissement"'
# Quarto's class "hidden", lifted by its script once the page has loaded.
_HIDDEN = re.compile(r'(class="[^"]*?)\s*(?<![\w-])hidden(?![\w-])')
_SKIP_LINK = re.compile(r'[ \t]*<a class="lien-evitement"[^>]*>[^<]*</a>[ \t]*\r?\n?')


def _header_bounds(html: str) -> tuple[int, int]:
    start = html.find(HEADER)
    if start < 0:
        raise ValueError("en-tête fixe (header#quarto-header) introuvable")
    end = html.find("</header>", start)
    if end < 0:
        raise ValueError("fin de l'en-tête fixe introuvable")
    return start, end


def move_notice(html: str) -> str:
    """The notice just after the fixed header; unchanged if there is none or it is done."""
    if NOTICE not in html:
        return html
    if html.count(NOTICE) != 1:
        raise ValueError(f"{html.count(NOTICE)} annonces trouvées, 1 attendue")
    start, end = _header_bounds(html)
    notice = html.find(NOTICE)
    if notice > end:
        return html
    if notice < start:
        raise ValueError("annonce avant l'en-tête fixe (balisage de Quarto changé ?)")
    block = html[notice:end].rstrip()
    if block.count("<div") != block.count("</div>") or not block.endswith("</div>"):
        raise ValueError("l'annonce n'est pas le dernier élément de l'en-tête (balisage de Quarto changé ?)")
    tag_end = block.index(">")
    tag = _HIDDEN.sub(r"\1", block[:tag_end])
    block = NOTICE + LABEL + tag[len(NOTICE) :] + block[tag_end:]
    close = end + len("</header>")
    return html[:notice].rstrip(" \t") + html[end:close] + "\n" + block + html[close:]


def move_skip_link(html: str) -> str:
    """The skip link just before the fixed header; unchanged if there is none or it is done."""
    links = list(_SKIP_LINK.finditer(html))
    if not links:
        return html
    if len(links) != 1:
        raise ValueError(f"{len(links)} liens d'évitement trouvés, 1 attendu")
    start, _ = _header_bounds(html)
    link = links[0]
    if link.start() < start:
        return html
    line_start = html.rfind("\n", 0, start) + 1
    tag = link.group(0).strip()
    without = html[: link.start()] + html[link.end() :]
    return without[:line_start] + tag + "\n" + without[line_start:]


def patch(html: str) -> str:
    """The page with the notice after the fixed header and the skip link before it."""
    return move_skip_link(move_notice(html))


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
            print(f"entete_postprocess : {path} : {error}", file=sys.stderr)
            return 1
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(f"entete_postprocess : {changed} page(s) corrigée(s) (avertissement et lien d'évitement).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
