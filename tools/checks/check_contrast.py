"""Check the WCAG contrast of every text/background pair of the design tokens.

The colours live in assets/theme.scss ($name: #hex;). The pairs actually used on
the site, with their minimum ratio, are listed in tools/checks/contrast_pairs.yml.

Usage: python tools/checks/check_contrast.py
Exit code 1 if a pair is below its minimum or names an unknown token.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "assets" / "theme.scss"
PAIRS = Path(__file__).resolve().parent / "contrast_pairs.yml"

_TOKEN = re.compile(r"^\s*\$([\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;", re.MULTILINE)


def parse_scss_tokens(scss: str) -> dict[str, str]:
    """Return the SCSS variables whose value is a literal 6-digit hex colour."""
    return {name: value.lower() for name, value in _TOKEN.findall(scss)}


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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tokens = parse_scss_tokens(THEME.read_text(encoding="utf-8"))
    pairs = yaml.safe_load(PAIRS.read_text(encoding="utf-8"))["paires"]
    failures = check_pairs(tokens, pairs)
    for pair in pairs:
        if pair["texte"] in tokens and pair["fond"] in tokens:
            ratio = contrast_ratio(tokens[pair["texte"]], tokens[pair["fond"]])
            print(f"  {pair['texte']:>14} / {pair['fond']:<14} {ratio:5.2f}:1  {pair.get('usage', '')}")
    if failures:
        print("\nÉCHEC du contrôle des contrastes :")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"\nContrastes : {len(pairs)} paires conformes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
