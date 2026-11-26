"""Check that every section heading of a rendered page appears in its table of contents.

Pandoc lists only the headings that open a section; a heading inside an ordinary div
(for example the old ::: {.texte-patient} wrapper) silently drops out of "Sur cette page"
(user panel, round 2). This reads the rendered pages in _site/ and reports each h2 or h3
that has an id but no link in the page's table of contents. Headings inside member cards
(.carte) and listing titles are not sections and are skipped; pages without a table of
contents are not checked.

Usage: python tools/checks/check_toc.py [path/to/_site]   (after quarto render)
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}
HEADINGS = {"h2", "h3"}
NOT_SECTIONS = {"carte", "quarto-listing", "listing-title"}
IGNORED_IDS = {"toc-title"}


class _TocParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict[str, str]]] = []
        self.has_toc = False
        self.toc_targets: set[str] = set()
        self.heading_ids: list[str] = []

    def _inside(self, test) -> bool:
        return any(test(tag, attrs) for tag, attrs in self.stack)

    def handle_starttag(
        self, tag: str, attrs_list: list[tuple[str, str | None]]
    ) -> None:
        attrs = {k: v or "" for k, v in attrs_list}
        in_toc = self._inside(lambda t, a: t == "nav" and a.get("id") == "TOC")
        if tag == "nav" and attrs.get("id") == "TOC":
            self.has_toc = True
        elif in_toc and tag == "a" and attrs.get("href", "").startswith("#"):
            self.toc_targets.add(attrs["href"][1:])
        elif tag in HEADINGS and not in_toc and self._is_section_heading(attrs):
            heading_id = attrs.get("id") or self._enclosing_section_id()
            if heading_id and heading_id not in IGNORED_IDS:
                self.heading_ids.append(heading_id)
        if tag not in VOID:
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def _is_section_heading(self, attrs: dict[str, str]) -> bool:
        classes = set(attrs.get("class", "").split())
        if classes & NOT_SECTIONS:
            return False
        return not self._inside(
            lambda t, a: bool(set(a.get("class", "").split()) & NOT_SECTIONS)
        )

    def _enclosing_section_id(self) -> str:
        for tag, attrs in reversed(self.stack):
            if tag == "section" and attrs.get("id"):
                return attrs["id"]
        return ""


def missing_from_toc(html: str) -> list[str]:
    """Ids of the section headings of a page that its table of contents does not link to."""
    parser = _TocParser()
    parser.feed(html)
    if not parser.has_toc:
        return []
    return [i for i in parser.heading_ids if i not in parser.toc_targets]


def main(argv: list[str]) -> int:
    site = Path(argv[1]) if len(argv) > 1 else ROOT / "_site"
    if not site.is_dir():
        print(f"check_toc : {site} absent ; lancez d'abord quarto render.")
        return 1
    pages = [p for p in sorted(site.rglob("*.html")) if "site_libs" not in p.parts]
    failures = 0
    for page in pages:
        missing = missing_from_toc(page.read_text(encoding="utf-8"))
        if missing:
            failures += 1
            print(
                f"{page.relative_to(site).as_posix()} : absents du sommaire : {', '.join(missing)}"
            )
    print(f"check_toc : {len(pages)} pages, {failures} sommaire(s) incomplet(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
