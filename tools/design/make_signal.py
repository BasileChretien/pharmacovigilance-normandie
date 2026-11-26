"""Draw the home-page figure: the towns of Normandy, linked to the two CRPV.

Reads data/normandie-carte.json (written by tools/design/fetch_normandie.py) and writes
_includes/signal.md, included by index.qmd. Each dot is a town; its area grows with the
population. The map shows the five departments, tinted by the centre that covers them
(Caen: Calvados, Manche, Orne; Rouen: Eure, Seine-Maritime). Towns of 10,000 inhabitants
or more are linked to their centre, and pulses travel along the links (CSS, theme.scss;
started and paused by assets/js/accueil.js). Deterministic: same data, same figure.
Usage: python tools/design/make_signal.py
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Callable
from pathlib import Path

from fetch_normandie import simplify

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "normandie-carte.json"
OUT = ROOT / "_includes" / "signal.md"

WIDTH, HEIGHT, MARGIN = 560, 440, 14
SEED = 14  # Calvados
R_MIN, R_SCALE = 1.8, 0.027  # radius = R_SCALE * sqrt(population), at least R_MIN
GAP = 1.5  # minimum gap between two dots, in figure units
OUTLINE_TOLERANCE = 1.2  # outline simplification, in figure units
LINK_MIN = 10_000  # towns linked to their centre
SPEED = 95.0  # pulse speed, figure units per second
CRPV = {"14": "Caen", "50": "Caen", "61": "Caen", "27": "Rouen", "76": "Rouen"}

CYAN, GREEN, INK, HALO = "#19a6e3", "#2bcf8c", "#10283a", "#eef6fa"
DOT, LINK = (
    "#7f9fb3",
    "#9bb9cb",
)  # small towns and resting links: visible on the tinted map
FILL = {
    "Caen": "#d3e9f5",
    "Rouen": "#d4efe2",
}  # decorative tints of the two territories

Point = tuple[float, float]


def make_projection(
    departements: list[dict], width: float, height: float, margin: float
) -> Callable[[float, float], Point]:
    """Equirectangular projection centred on the region, scaled to fit the frame."""
    lons = [p[0] for d in departements for ring in d["contours"] for p in ring]
    lats = [p[1] for d in departements for ring in d["contours"] for p in ring]
    k = math.cos(math.radians((min(lats) + max(lats)) / 2))
    span_x, span_y = (max(lons) - min(lons)) * k, max(lats) - min(lats)
    scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)
    off_x = (width - span_x * scale) / 2
    off_y = (height - span_y * scale) / 2
    lon0, lat1 = min(lons), max(lats)

    def project(lon: float, lat: float) -> Point:
        return off_x + (lon - lon0) * k * scale, off_y + (lat1 - lat) * scale

    return project


def radius(population: int) -> float:
    """Dot radius: the area grows with the population."""
    return max(R_MIN, R_SCALE * math.sqrt(population))


def select_towns(
    villes: list[dict], project: Callable[[float, float], Point]
) -> list[dict]:
    """Towns to draw, with their position: the two centres first, then by size, and no
    town whose dot would sit on a bigger one (suburbs of Rouen and Caen)."""
    hubs = set(CRPV.values())
    ordered = sorted(villes, key=lambda v: (v["nom"] not in hubs, -v["population"]))
    kept: list[dict] = []
    for v in ordered:
        x, y = project(v["lon"], v["lat"])
        r = radius(v["population"])
        clear = all(
            math.dist((x, y), (k["x"], k["y"])) >= r + k["r"] + GAP for k in kept
        )
        if v["nom"] in hubs or clear:
            kept.append({**v, "x": x, "y": y, "r": r})
    return kept


def links(towns: list[dict]) -> list[tuple[dict, dict]]:
    """(town, centre) pairs: each town of LINK_MIN inhabitants or more, to its centre."""
    hubs = {t["nom"]: t for t in towns if t["nom"] in CRPV.values()}
    return [
        (t, hubs[CRPV[t["departement"]]])
        for t in towns
        if t["population"] >= LINK_MIN
        and t["nom"] not in hubs
        and CRPV.get(t["departement"]) in hubs
    ]


def _path(ring: list[list[float]], project: Callable[[float, float], Point]) -> str:
    points = simplify([list(project(lon, lat)) for lon, lat in ring], OUTLINE_TOLERANCE)
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points) + " Z"


def _map(data: dict, project: Callable[[float, float], Point]) -> list[str]:
    return [
        f'<path class="signal-carte" d="{_path(ring, project)}" fill="{FILL[dep["crpv"]]}" '
        'stroke="#ffffff" stroke-width="1.5" stroke-linejoin="round"/>'
        for dep in data["departements"]
        for ring in dep["contours"]
    ]


def _links(pairs: list[tuple[dict, dict]]) -> list[str]:
    rng = random.Random(SEED)
    parts = []
    for i, (town, hub) in enumerate(pairs):
        coords = f'x1="{town["x"]:.1f}" y1="{town["y"]:.1f}" x2="{hub["x"]:.1f}" y2="{hub["y"]:.1f}"'
        travel = math.dist((town["x"], town["y"]), (hub["x"], hub["y"])) / SPEED
        delay = 1.2 + rng.uniform(0, 4)
        period = travel / 0.7 + rng.uniform(
            0, 1.2
        )  # the pulse travels for 70 % of the period
        parts += [
            f'<line class="signal-lien" style="--d:{0.1 + i * 0.05:.2f}s" pathLength="1" {coords} '
            f'stroke="{LINK}" stroke-width="1.2" stroke-linecap="round"/>',
            f'<line class="signal-flux" style="--d:{delay:.2f}s;--t:{period:.2f}s" pathLength="1" {coords} '
            'stroke="url(#signal-degrade)" stroke-width="3" stroke-linecap="round"/>',
        ]
    return parts


def _hub(hub: dict, j: int) -> list[str]:
    x, y, r = hub["x"], hub["y"], hub["r"]
    return [
        f'<circle class="signal-anneau" style="--d:{j * 1.3:.1f}s" cx="{x:.1f}" cy="{y:.1f}" r="{r + 8:.1f}" '
        f'fill="none" stroke="{GREEN}" stroke-width="3"/>',
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="url(#signal-degrade)" stroke="#ffffff" stroke-width="3"/>',
        f'<text x="{x:.1f}" y="{y - r - 12:.1f}" text-anchor="middle" '
        'font-family="Atkinson Hyperlegible Mono Variable, monospace" font-size="15" font-weight="700" '
        f'fill="{INK}" stroke="{HALO}" stroke-width="6" stroke-linejoin="round" paint-order="stroke">'
        f"CRPV {hub['nom']}</text>",
    ]


def svg(data: dict) -> str:
    project = make_projection(data["departements"], WIDTH, HEIGHT, MARGIN)
    towns = select_towns(data["villes"], project)
    pairs = links(towns)
    linked = {t["nom"] for t, _ in pairs}
    hubs = [t for t in towns if t["nom"] in CRPV.values()]
    parts = [
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" aria-hidden="true" focusable="false">',
        "<defs>",
        f'<linearGradient id="signal-degrade" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{WIDTH}" y2="{HEIGHT}">',
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{GREEN}"/>',
        "</linearGradient>",
        "</defs>",
        *_map(data, project),
        *_links(pairs),
    ]
    for t in towns:
        if t["nom"] not in CRPV.values():
            fill = "url(#signal-degrade)" if t["nom"] in linked else DOT
            parts.append(
                f'<circle cx="{t["x"]:.1f}" cy="{t["y"]:.1f}" r="{t["r"]:.1f}" fill="{fill}"/>'
            )
    for j, hub in enumerate(hubs):
        parts += _hub(hub, j)
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!-- Generated by tools/design/make_signal.py from data/normandie-carte.json: "
        "edit the script, not this file. -->\n```{=html}\n" + svg(data) + "\n```\n",
        encoding="utf-8",
    )
    project = make_projection(data["departements"], WIDTH, HEIGHT, MARGIN)
    towns = select_towns(data["villes"], project)
    print(f"{OUT.relative_to(ROOT)} : {len(towns)} villes, {len(links(towns))} liens.")


if __name__ == "__main__":
    main()
