"""Check the WCAG contrast of every text/background pair of the design tokens.

The colours live in assets/theme.scss ($name: #hex !default;); the dark theme,
assets/theme-sombre.scss, gives some of them another value. The pairs actually used on
the site, with their minimum ratio, are listed in tools/checks/contrast_pairs.yml. Each
pair is checked in both themes ("clair", "sombre"), unless it names its themes.

Usage: python tools/checks/check_contrast.py
Exit code 1 if a pair is below its minimum or names an unknown token or theme.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "assets" / "theme.scss"
THEME_SOMBRE = ROOT / "assets" / "theme-sombre.scss"
PAIRS = Path(__file__).resolve().parent / "contrast_pairs.yml"
THEMES = ("clair", "sombre")

_TOKEN = re.compile(r"^\s*\$([\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*(?:!default\s*)?;", re.MULTILINE)


def parse_scss_tokens(scss: str) -> dict[str, str]:
    """Return the SCSS variables whose value is a literal 6-digit hex colour."""
    return {name: value.lower() for name, value in _TOKEN.findall(scss)}


def unread_dark_tokens(light_scss: str, dark_scss: str) -> list[str]:
    """Light tokens that the dark file sets in a form this check cannot read (#fff, a Sass
    function): their pairs would be checked on the light value and pass."""
    light = parse_scss_tokens(light_scss)
    dark = parse_scss_tokens(dark_scss)
    assigned = re.findall(r"^\s*\$([\w-]+)\s*:", dark_scss, re.MULTILINE)
    return sorted({name for name in assigned if name in light and name not in dark})


def theme_tokens(light_scss: str, dark_scss: str) -> dict[str, dict[str, str]]:
    """The tokens of each theme: the dark one is the light one, overridden by its file."""
    light = parse_scss_tokens(light_scss)
    return {"clair": light, "sombre": {**light, **parse_scss_tokens(dark_scss)}}


def _linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = sorted((relative_luminance(fg), relative_luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def check_pairs(tokens: dict[str, str], pairs: list[dict]) -> list[str]:
    """Return one message per failing pair; an empty list means all pass."""
    failures = []
    for pair in pairs:
        fg_name, bg_name = pair["texte"], pair["fond"]
        minimum = float(pair.get("minimum", 4.5))
        missing = [n for n in (fg_name, bg_name) if n not in tokens]
        if missing:
            failures.append(f"jeton inconnu : {', '.join(missing)}")
            continue
        ratio = contrast_ratio(tokens[fg_name], tokens[bg_name])
        if ratio < minimum:
            usage = pair.get("usage", "")
            failures.append(
                f"{fg_name} sur {bg_name} : {ratio:.2f}:1 < {minimum}:1 ({usage})"
            )
    return failures


def pair_themes(pair: dict) -> list[str]:
    return list(pair.get("themes", THEMES))


def check_themes(themes: dict[str, dict[str, str]], pairs: list[dict]) -> list[str]:
    """Check each pair in each of its themes; messages start with the theme's name."""
    failures = []
    for pair in pairs:
        for theme in pair_themes(pair):
            if theme not in themes:
                failures.append(f"thème inconnu « {theme} » ({pair['texte']} sur {pair['fond']})")
                continue
            failures.extend(f"{theme} : {m}" for m in check_pairs(themes[theme], [pair]))
    return failures


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    light_scss, dark_scss = THEME.read_text(encoding="utf-8"), THEME_SOMBRE.read_text(encoding="utf-8")
    themes = theme_tokens(light_scss, dark_scss)
    pairs = yaml.safe_load(PAIRS.read_text(encoding="utf-8"))["paires"]
    failures = [
        f"sombre : ${name} illisible dans assets/theme-sombre.scss (écrire #rrggbb)"
        for name in unread_dark_tokens(light_scss, dark_scss)
    ] + check_themes(themes, pairs)
    for pair in pairs:
        ratios = []
        for theme in pair_themes(pair):
            tokens = themes.get(theme, {})
            if pair["texte"] in tokens and pair["fond"] in tokens:
                ratios.append(f"{theme} {contrast_ratio(tokens[pair['texte']], tokens[pair['fond']]):5.2f}:1")
        print(f"  {pair['texte']:>16} / {pair['fond']:<14} {'  '.join(ratios):<30} {pair.get('usage', '')}")
    if failures:
        print("\nÉCHEC du contrôle des contrastes :")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"\nContrastes : {len(pairs)} paires conformes (thèmes clair et sombre).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
