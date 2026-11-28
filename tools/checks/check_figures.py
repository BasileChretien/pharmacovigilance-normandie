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

And what keeps a figure readable in the dark (docs/mode-sombre.md). Dark Reader darkens
the fill attribute of a large shape like a background and lightens the fill of a <text>,
and of a shape of 32 px or less, like a text colour. So:

- the <svg> is fill="currentColor": text without a fill of its own takes the page's text
  colour (a fill on <svg>, darkened as a background, left that text dark on dark);
- a text takes its colour on itself, not from a coloured group, and no <tspan> is coloured
  (Dark Reader measures it like a shape);
- no text sits on a filled shape that would be 32 px or less on a phone (Dark Reader
  lightens both): such a disc is outlined, or the shape is larger;
- a pattern holds no filled rectangle (its tile background, which Dark Reader cannot
  measure): the zone's colour is a shape of its own, the pattern only its lines;
- every colour of a figure, of the home-page map and of the frequency grids has a dark
  value in assets/theme-sombre.scss, and a token's dark value is a token of that light value.

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
THEME_SOMBRE = ROOT / "assets" / "theme-sombre.scss"
# Other drawings whose colours the dark theme maps (their own rules live with their code).
DRAWINGS = (ROOT / "_includes" / "signal.md", ROOT / "assets" / "js" / "frequences.js")
EXCLUDED_DIRS = {"_site", "_templates", "docs", "node_modules", ".quarto", ".venv", "tests", "tools"}

MAX_WIDTH = 440  # units = px on a desktop; 375 px phone: 16 units -> about 12 px
MIN_FONT = 16
SITE_FONT = "Atkinson Hyperlegible Next Variable"
ROOT_FILL = "currentColor"  # the text colour of the page (.figure-pv svg in theme.scss)
ROOT_FILL_TOKEN = "pv-ink"
# Dark Reader treats a filled shape of 32 px or less as text colour. A figure drawn on a
# 320 px phone shrinks to about 0.7: a shape carrying text must exceed 46 units.
SMALL_SHAPE = 46
# Colours a text may take (contrast checked in tools/checks/contrast_pairs.yml).
TEXT_TOKENS = {"pv-ink", "pv-ink-quiet", "pv-signal", "pv-signal-dark", "pv-alert", "pv-green-ink", "pv-amber", "pv-paper"}
COLOUR_ATTRS = ("fill", "stroke", "stop-color", "flood-color", "lighting-color", "color")
FORBIDDEN_TAGS = {"script", "style", "title", "image", "foreignObject", "iframe", "a"}
FORBIDDEN_ATTRS = {"style", "class", "opacity", "fill-opacity", "stroke-opacity"}
TEXT_TAGS = {"text", "tspan", "textPath"}
SHAPE_TAGS = {"rect", "circle", "ellipse"}
SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"

_SHORTCODE = re.compile(r"\{\{<\s*figure-svg\s+(.*?)\s*>\}\}", re.DOTALL)
_KWARG = re.compile(r'([\w-]+)="([^"]*)"')
_HEX = re.compile(r"#[0-9a-fA-F]{6}")
_HEX_ANYWHERE = re.compile(r"#[0-9a-fA-F]{6}\b")
_URL = re.compile(r"url\((.*?)\)")
_TRANSLATE = re.compile(r"\s*translate\(\s*(-?[0-9.]+)(?:[\s,]+(-?[0-9.]+))?\s*\)\s*")
_DARK_ENTRY = re.compile(r'"(#[0-9a-fA-F]{6})"\s*:\s*(\$[\w-]+|#[0-9a-fA-F]{6})')


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _number(value: str) -> float | None:
    match = re.fullmatch(r"\s*([0-9.]+)(px)?\s*", value)
    return float(match.group(1)) if match else None


def _float(node: ET.Element, attr: str) -> float:
    value = (node.get(attr) or "0").replace(",", " ").split()
    try:
        return float(value[0]) if value else 0.0
    except ValueError:
        return 0.0


def hex_tokens(tokens: dict[str, str]) -> dict[str, str]:
    """Token of each hex value; when two tokens share a value, the first one named."""
    by_hex: dict[str, str] = {}
    for token, value in tokens.items():
        by_hex.setdefault(value.lower(), token)
    return by_hex


def _colour_problems(attr: str, value: str, by_hex: dict[str, str]) -> list[str]:
    value = value.strip()
    if value in ("none", "transparent"):
        return []
    url = _URL.fullmatch(value)
    if url:
        return [] if url.group(1).startswith("#") else [f"{attr}={value} : lien hors du fichier"]
    if _HEX.fullmatch(value) and value.lower() in by_hex:
        return []
    if value == ROOT_FILL:
        return [f"{attr}={ROOT_FILL} : réservé à <svg> (écrire la couleur en hexadécimal)"]
    return [f"{attr}={value} : couleur hors des jetons de assets/theme.scss"]


def _offset(node: ET.Element, origin: tuple[float, float] | None) -> tuple[float, float] | None:
    """Origin of a node's children: translate() adds up; any other transform is unknown."""
    transform = node.get("transform")
    if origin is None or not transform:
        return origin
    match = _TRANSLATE.fullmatch(transform)
    if not match:
        return None
    return origin[0] + float(match.group(1)), origin[1] + float(match.group(2) or 0)


def _shape_box(node: ET.Element, origin: tuple[float, float]) -> tuple[float, float, float, float]:
    tag, (ox, oy) = _local(node.tag), origin
    if tag == "rect":
        return ox + _float(node, "x"), oy + _float(node, "y"), _float(node, "width"), _float(node, "height")
    rx = _float(node, "r") if tag == "circle" else _float(node, "rx")
    ry = _float(node, "r") if tag == "circle" else _float(node, "ry")
    return ox + _float(node, "cx") - rx, oy + _float(node, "cy") - ry, 2 * rx, 2 * ry


def _text_point(node: ET.Element, origin: tuple[float, float], size: float) -> tuple[float, float]:
    """Middle of the first letters of a text, roughly: where it sits on a shape."""
    x, y = origin[0] + _float(node, "x"), origin[1] + _float(node, "y")
    anchor = node.get("text-anchor", "start")
    shift = {"start": 0.3 * size, "end": -0.3 * size}.get(anchor, 0.0)
    return x + shift, y - 0.35 * size


def _texts_on_small_shapes(shapes: list, texts: list) -> list[str]:
    problems = []
    for label, (px, py) in texts:
        for x, y, w, h in shapes:
            if x - 1 <= px <= x + w + 1 and y - 1 <= py <= y + h + 1:
                problems.append(
                    f"texte « {label} » sur une petite forme pleine ({w:g} × {h:g}) : Dark Reader "
                    f"l'éclaircit comme le texte ; bord seul (fill=\"none\") ou plus de {SMALL_SHAPE} unités"
                )
                break
    return problems


def check_svg(name: str, text: str, tokens: dict[str, str]) -> list[str]:
    """Return one message per broken rule in the SVG file of figure `name`."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        return [f"XML mal formé : {error}"]
    if _local(root.tag) != "svg":
        return ["l'élément racine n'est pas <svg>"]
    by_hex = hex_tokens(tokens)
    problems: list[str] = []
    shapes: list[tuple[float, float, float, float]] = []
    texts: list[tuple[str, tuple[float, float]]] = []

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
    if root.get("fill") != ROOT_FILL:
        problems.append(
            f"fill=\"{ROOT_FILL}\" attendu sur <svg> : Dark Reader assombrit un fill posé sur <svg> "
            "comme un fond, et le texte qui en hérite devient sombre sur sombre"
        )
    by_hex_root = {**by_hex, ROOT_FILL.lower(): ROOT_FILL_TOKEN}

    def walk(node: ET.Element, fill: str | None, source: str, size: float | None,
             origin: tuple[float, float] | None, in_pattern: bool) -> None:
        tag = _local(node.tag)
        label = "".join(node.itertext()).strip()[:40]
        if tag in FORBIDDEN_TAGS:
            problems.append(f"élément <{tag}> interdit")
        for attr, value in node.attrib.items():
            local = _local(attr)
            if local in FORBIDDEN_ATTRS or local.startswith("on"):
                problems.append(f"attribut {local} interdit sur <{tag}>")
            if local in COLOUR_ATTRS and not (node is root and local == "fill"):
                problems.extend(_colour_problems(local, value, by_hex))
            if local == "id" and not value.startswith(f"{name}-"):
                problems.append(f"id « {value} » : doit commencer par « {name}- »")
            if attr in ("href", XLINK_HREF) and not value.startswith("#"):
                problems.append(f"lien « {value} » hors du fichier")
        own_fill = node.get("fill")
        if own_fill is not None and tag in ("tspan", "textPath"):
            problems.append(f"<{tag}> coloré « {label} » : colorer le <text> entier (Dark Reader mesure un <{tag}> comme une forme)")
        if own_fill is not None:
            fill = own_fill
            source = "text" if tag in TEXT_TAGS else ("root" if node is root else "group")
        if node.get("font-size") is not None:
            size = _number(node.get("font-size", ""))
            if size is None or size < MIN_FONT:
                problems.append(f"font-size {node.get('font-size')} sur <{tag}> : {MIN_FONT} au moins")
        origin = _offset(node, origin)
        in_pattern = in_pattern or tag == "pattern"
        if in_pattern and tag == "rect" and (own_fill or "none") != "none":
            problems.append("rectangle plein dans un motif : le fond d'une zone est une forme à part, le motif ne garde que ses traits")
        if tag in SHAPE_TAGS and not in_pattern and origin is not None and (fill or "none") != "none" \
                and not (fill or "").startswith("url("):
            box = _shape_box(node, origin)
            if box[2] <= SMALL_SHAPE and box[3] <= SMALL_SHAPE:
                shapes.append(box)
        if tag in TEXT_TAGS:
            token = by_hex_root.get((fill or "").lower())
            if token is None:
                problems.append(f"texte « {label} » sans couleur de jeton")
            elif token not in TEXT_TOKENS:
                problems.append(f"texte « {label} » en {token} : couleur décorative, jamais du texte")
            if source == "group":
                problems.append(f"texte « {label} » coloré par son groupe : poser fill sur le <text> (Dark Reader assombrit le groupe comme un fond)")
            if size is None:
                problems.append(f"texte « {label} » sans font-size")
            elif tag == "text" and origin is not None:
                texts.append((label, _text_point(node, origin, size)))
        for child in node:
            walk(child, fill, source, size, origin, in_pattern)

    walk(root, None, "root", None, (0.0, 0.0), False)
    problems.extend(_texts_on_small_shapes(shapes, texts))
    return problems


def parse_dark_map(scss: str) -> dict[str, str]:
    """The $pv-figures-sombre map of theme-sombre.scss: light hex -> dark token or hex."""
    return {key.lower(): value.lower() for key, value in _DARK_ENTRY.findall(scss)}


def check_dark_map(dark: dict[str, str], tokens: dict[str, str], used: dict[str, list[str]]) -> list[str]:
    """Every colour used has a dark value; a token's dark value is a token of the same
    light value (two tokens may share one: pv-ecume for the footer, pv-eau for water)."""
    names: dict[str, list[str]] = {}
    for token, value in tokens.items():
        names.setdefault(value.lower(), []).append(token)
    problems = []
    for colour in sorted(used):
        if colour not in dark:
            where = ", ".join(sorted(set(used[colour]))[:3])
            problems.append(f"{colour} ({where}) : pas de valeur sombre dans $pv-figures-sombre (assets/theme-sombre.scss)")
    for colour, value in sorted(dark.items()):
        allowed = [f"${t}" for t in names.get(colour, [])]
        if allowed and value not in allowed:
            problems.append(f"{colour} est {names[colour][0]} : sa valeur sombre doit être {' ou '.join(allowed)}, pas {value}")
    return problems


def colours_in(text: str) -> set[str]:
    """Hex colours written in a drawing, its generator output or its script."""
    return {c.lower() for c in _HEX_ANYWHERE.findall(text)}


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
    used: dict[str, list[str]] = {}
    for page in site_pages():
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT).as_posix()
        for code in parse_shortcodes(text):
            placed.setdefault(code["nom"], []).append(rel)
        if problems := check_page(text, figures):
            report[rel] = problems
    for svg in files:
        text = svg.read_text(encoding="utf-8")
        for colour in colours_in(text):
            used.setdefault(colour, []).append(svg.stem)
        problems = check_svg(svg.stem, text, tokens)
        pages = sorted(set(placed.get(svg.stem, [])))
        if not pages:
            problems.append("figure placée sur aucune page")
        elif len(pages) > 1:
            problems.append(f"figure placée sur plusieurs pages : {', '.join(pages)}")
        if problems:
            report[svg.relative_to(ROOT).as_posix()] = problems
    for drawing in DRAWINGS:
        if drawing.exists():
            for colour in colours_in(drawing.read_text(encoding="utf-8")):
                used.setdefault(colour, []).append(drawing.name)
    dark = parse_dark_map(THEME_SOMBRE.read_text(encoding="utf-8"))
    if problems := check_dark_map(dark, tokens, used):
        report[THEME_SOMBRE.relative_to(ROOT).as_posix()] = problems
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
