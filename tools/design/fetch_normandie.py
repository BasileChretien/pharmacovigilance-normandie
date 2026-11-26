"""Fetch the data behind the home-page map: department outlines and towns of Normandy.

Writes data/normandie-carte.json, read by tools/design/make_signal.py (which stays
offline and deterministic). Run by hand when the sources change:
    python tools/design/fetch_normandie.py

Sources (both under the Licence Ouverte / Open Licence 2.0):
- outlines: Etalab, contours administratifs 2024 (from IGN Admin Express), 100 m version;
- towns: geo.api.gouv.fr, communes with their INSEE legal population and centre.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "normandie-carte.json"

CONTOURS_URL = "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson/departements-100m.geojson"
COMMUNES_URL = "https://geo.api.gouv.fr/departements/{code}/communes?fields=nom,code,population,centre&format=json"

# Department -> regional pharmacovigilance centre that covers it.
CRPV = {"14": "Caen", "50": "Caen", "61": "Caen", "27": "Rouen", "76": "Rouen"}
MIN_POPULATION = 5000
TOLERANCE_DEG = (
    0.003  # outline simplification, about 300 m: invisible at the figure's size
)


def _get_json(url: str) -> object:
    request = urllib.request.Request(
        url, headers={"User-Agent": "pharmacovigilance-normandie-build"}
    )
    # Only the two fixed https URLs above are ever opened.
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def _distance_to_segment(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def simplify(points: list[list[float]], tolerance: float) -> list[list[float]]:
    """Douglas-Peucker simplification of a line (iterative, keeps both ends)."""
    if len(points) < 3:
        return points
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        index, worst = None, tolerance
        for i in range(first + 1, last):
            d = _distance_to_segment(points[i], points[first], points[last])
            if d > worst:
                index, worst = i, d
        if index is not None:
            keep.add(index)
            stack += [(first, index), (index, last)]
    return [[round(x, 4), round(y, 4)] for i, (x, y) in enumerate(points) if i in keep]


def outer_rings(geometry: dict) -> list[list[list[float]]]:
    """Outer ring of each polygon (holes are not needed for a background map)."""
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    return [polygon[0] for polygon in geometry["coordinates"]]


def main() -> int:
    contours = _get_json(CONTOURS_URL)
    departements = []
    for feature in contours["features"]:
        code = feature["properties"]["code"]
        if code in CRPV:
            rings = [
                simplify(r, TOLERANCE_DEG) for r in outer_rings(feature["geometry"])
            ]
            departements.append(
                {
                    "code": code,
                    "nom": feature["properties"]["nom"],
                    "crpv": CRPV[code],
                    "contours": rings,
                }
            )
    villes = []
    for code in sorted(CRPV):
        for commune in _get_json(COMMUNES_URL.format(code=code)):
            if (commune.get("population") or 0) >= MIN_POPULATION and commune.get(
                "centre"
            ):
                lon, lat = commune["centre"]["coordinates"]
                villes.append(
                    {
                        "nom": commune["nom"],
                        "code": commune["code"],
                        "departement": code,
                        "population": commune["population"],
                        "lon": lon,
                        "lat": lat,
                    }
                )
    villes.sort(key=lambda v: -v["population"])
    data = {
        "sources": {
            "contours": CONTOURS_URL,
            "villes": COMMUNES_URL.format(code="{code}"),
            "licence": "Licence Ouverte / Open Licence 2.0 (Etalab)",
            "consulte_le": dt.datetime.now(dt.timezone.utc).date().isoformat(),
            "population_minimale": MIN_POPULATION,
        },
        "departements": sorted(departements, key=lambda d: d["code"]),
        "villes": villes,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    points = sum(len(r) for d in departements for r in d["contours"])
    print(
        f"{OUT.relative_to(ROOT)} : {len(departements)} départements ({points} points), {len(villes)} villes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
