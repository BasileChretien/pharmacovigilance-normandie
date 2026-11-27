"""Check the figures of the site and where they are placed.

Figures are hand-authored SVG files in assets/img/figures/, inlined in the pages by the
figure-svg shortcode (assets/filters/figure-svg.lua) so that they use the self-hosted
fonts. The style rules are in docs/regles-redaction.md, section 5. This check enforces
the measurable ones:

- each SVG is well-formed, as wide as its viewBox and at most MAX_WIDTH wide (it is
  drawn at 1 unit = 1 px, so its text stays readable on a 375 px phone);
- colours are design tokens of assets/theme.scss, and text only takes a text colour;
- text is at least MIN_FONT units, in the site's font;
- ids start with the figure's name (several figures may share a page), links stay
  inside the file, and there is no script, style, opacity or title (the shortcode adds
  the title from the page's alternative text);
- each shortcode names an existing figure, with an alternative text and a caption, and
  each figure is placed once.

Usage: python tools/checks/check_figures.py
Exit code 1 if a rule is broken.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from check_contrast import parse_scss_tokens

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "assets" / "img" / "figures"
THEME = ROOT / "assets" / "theme.scss"
EXCLUDED_DIRS = {"_site", "_templates", "docs", "node_modules", ".quarto", ".venv", "tests", "tools"}

MAX_WIDTH = 440  # units = px on a desktop; 375 px phone: 16 units -> about 12 px
MIN_FONT = 16
SITE_FONT = "Atkinson Hyperlegible Next Variable"
# Colours a text may take (contrast checked in tools/checks/contrast_pairs.yml).
TEXT_TOKENS = {"pv-ink", "pv-ink-quiet", "pv-signal", "pv-signal-dark", "pv-alert", "pv-green-ink", "pv-amber", "pv-paper"}
COLOUR_ATTRS = ("fill", "stroke", "stop-color", "flood-color", "lighting-color", "color")
FORBIDDEN_TAGS = {"script", "style", "title", "image", "foreignObject", "iframe", "a"}
FORBIDDEN_ATTRS = {"style", "class", "opacity", "fill-opacity", "stroke-opacity"}
SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"

_SHORTCODE = re.compile(r"\{\{<\s*figure-svg\s+(.*?)\s*>\}\}", re.DOTALL)
_KWARG = re.compile(r'([\w-]+)="([^"]*)"')
_HEX = re.compile(r"#[0-9a-fA-F]{6}")
_URL = re.compile(r"url\((.*?)\)")


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _number(value: str) -> float | None:
    match = re.fullmatch(r"\s*([0-9.]+)(px)?\s*", value)
    return float(match.group(1)) if match else None


def _colour_problems(attr: str, value: str, by_hex: dict[str, str]) -> list[str]:
    value = value.strip()
    if value in ("none", "transparent"):
        return []
    url = _URL.fullmatch(value)
    if url:
        return [] if url.group(1).startswith("#") else [f"{attr}={value} : lien hors du fichier"]
    if _HEX.fullmatch(value) and value.lower() in by_hex:
        return []
    return [f"{attr}={value} : couleur hors des jetons de assets/theme.scss"]


def check_svg(name: str, text: str, tokens: dict[str, str]) -> list[str]:
    """Return one message per broken rule in the SVG file of figure `name`."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        return [f"XML mal formé : {error}"]
    if _local(root.tag) != "svg":
        return ["l'élément racine n'est pas <svg>"]
    by_hex = {value.lower(): token for token, value in tokens.items()}
    problems: list[str] = []

    view = (root.get("viewBox") or "").split()
    width, height = _number(root.get("width", "")), _number(root.get("height", ""))
    if len(view) != 4 or view[:2] != ["0", "0"] or width is None or height is None:
        problems.append("viewBox « 0 0 L H » et attributs width et height attendus")
    elif (float(view[2]), float(view[3])) != (width, height):
        problems.append(f"width et height ({width:g} × {height:g}) différents du viewBox ({view[2]} × {view[3]})")
    if width is not None and width > MAX_WIDTH:
        problems.append(f"largeur {width:g} : {MAX_WIDTH} au plus")
    if SITE_FONT not in (root.get("font-family") or ""):
        problems.append(f"police : font-family doit commencer par « {SITE_FONT} » sur <svg>")

    def walk(node: ET.Element, fill: str | None, size: float | None) -> None:
        tag = _local(node.tag)
        if tag in FORBIDDEN_TAGS:
            problems.append(f"élément <{tag}> interdit")
        for attr, value in node.attrib.items():
            local = _local(attr)
            if local in FORBIDDEN_ATTRS or local.startswith("on"):
                problems.append(f"attribut {local} interdit sur <{tag}>")
            if local in COLOUR_ATTRS:
                problems.extend(_colour_problems(local, value, by_hex))
            if local == "id" and not value.startswith(f"{name}-"):
                problems.append(f"id « {value} » : doit commencer par « {name}- »")
            if attr in ("href", XLINK_HREF) and not value.startswith("#"):
                problems.append(f"lien « {value} » hors du fichier")
        fill = node.get("fill", fill)
        if node.get("font-size") is not None:
            size = _number(node.get("font-size", ""))
            if size is None or size < MIN_FONT:
                problems.append(f"font-size {node.get('font-size')} sur <{tag}> : {MIN_FONT} au moins")
        if tag in ("text", "tspan", "textPath"):
            token = by_hex.get((fill or "").lower())
            if token is None:
                problems.append(f"texte « {''.join(node.itertext())[:40]} » sans couleur de jeton")
            elif token not in TEXT_TOKENS:
                problems.append(f"texte « {''.join(node.itertext())[:40]} » en {token} : couleur décorative, jamais du texte")
            if size is None:
                problems.append(f"texte « {''.join(node.itertext())[:40]} » sans font-size")
        for child in node:
            walk(child, fill, size)

    walk(root, None, None)
    return problems


def parse_shortcodes(text: str) -> list[dict[str, str]]:
    """The figure-svg shortcodes of a page: name, then the keyword arguments."""
    found = []
    for match in _SHORTCODE.finditer(text):
        args = match.group(1)
        positional = _KWARG.sub("", args).split()
        entry = {"nom": positional[0] if positional else ""}
        entry.update(dict(_KWARG.findall(args)))
        found.append(entry)
    return found


def check_page(text: str, figures: set[str]) -> list[str]:
    """Return one message per broken rule in the figure shortcodes of a page."""
    problems = []
    names = []
    for code in parse_shortcodes(text):
        name = code["nom"]
        names.append(name)
        if name not in figures:
            problems.append(f"figure « {name} » : fichier assets/img/figures/{name}.svg absent")
        for key in ("alt", "legende"):
            if not code.get(key, "").strip():
                problems.append(f"figure « {name} » : {key} manquant ou vide")
    for name in sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"figure « {name} » placée plusieurs fois sur la page")
    return problems


def site_pages() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.qmd")
        if not any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts)
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tokens = parse_scss_tokens(THEME.read_text(encoding="utf-8"))
    files = sorted(FIGURES.glob("*.svg")) if FIGURES.exists() else []
    figures = {f.stem for f in files}
    report: dict[str, list[str]] = {}
    placed: dict[str, list[str]] = {}
    for page in site_pages():
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT).as_posix()
        for code in parse_shortcodes(text):
            placed.setdefault(code["nom"], []).append(rel)
        if problems := check_page(text, figures):
            report[rel] = problems
    for svg in files:
        problems = check_svg(svg.stem, svg.read_text(encoding="utf-8"), tokens)
        pages = sorted(set(placed.get(svg.stem, [])))
        if not pages:
            problems.append("figure placée sur aucune page")
        elif len(pages) > 1:
            problems.append(f"figure placée sur plusieurs pages : {', '.join(pages)}")
        if problems:
            report[svg.relative_to(ROOT).as_posix()] = problems
    for where, problems in report.items():
        print(f"\n{where}")
        for message in problems:
            print(f"  - {message}")
    if report:
        print(f"\nÉCHEC du contrôle des figures : {sum(map(len, report.values()))} problème(s).")
        return 1
    print(f"\nFigures : {len(files)} figures conformes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
