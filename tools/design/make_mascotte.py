"""Animate the mascot for each of its contexts.

Reads the hand-drawn assets/img/mascotte.svg and writes one variant per context in
assets/img/mascotte/: the same drawing, its parts grouped (whole body, head, eyes, arm and
horn, the horn's waves), with a pose and a short CSS animation of its own:

- accueil: beside « Déclarer », he raises the horn and sounds the alert, three pulses.
- vigiking: the bulletin's masthead: a hop, then the horn announces the issue.
- 404: lost: the horn leaves his lips, he looks left and right, a question mark pops up.
- recherche: a search found nothing: he scans, head tilted, his mouth says « hmm ».
- attente: the publications list is not filled yet: he waits, breathing, beside three dots.

Placed as an <img>, a variant cannot be paused from the page: every animation plays once and
ends within 5 s (WCAG 2.2.2), and only when the reader has not asked for reduced motion.
Without motion, each variant shows its context's pose. The waves of the horn show only where
he announces something. Checks: tests/test_mascotte_animations.py. Deterministic.

Usage: python tools/design/make_mascotte.py
"""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets" / "img" / "mascotte.svg"
OUT = ROOT / "assets" / "img" / "mascotte"
NS = "http://www.w3.org/2000/svg"
INK, WHITE = "#10283a", "#ffffff"

ET.register_namespace("", NS)

# Where each part turns or scales from (user units of the 240 x 280 drawing).
BASE_CSS = """
.m-corps, .m-ombre, .m-tete, .m-yeux, .m-bras, .m-onde, .m-extra, .m-point {
  transform-box: view-box;
}
.m-corps { transform-origin: 120px 262px; }
.m-ombre { transform-origin: 122px 266px; }
.m-tete { transform-origin: 120px 140px; }
.m-yeux { transform-origin: 120px 103px; }
.m-bras { transform-origin: 90px 142px; }
.m-onde { transform-origin: 48px 64px; }
.m-extra { transform-origin: 180px 66px; }
"""

# The horn away from the lips: the pose of the quiet contexts.
POSE_CALME = ".m-bras { transform: rotate(-12deg); }\n"

KEYFRAMES = {
    "m-lever": "from { transform: rotate(-14deg); } to { transform: none; }",
    "m-onde": "0% { opacity: 0; transform: scale(0.6); } "
    "60% { opacity: 1; transform: scale(1.05); } 100% { opacity: 1; transform: none; }",
    "m-cligne": "0%, 100% { transform: none; } 50% { transform: scaleY(0.1); }",
    "m-saut": "0%, 100% { transform: none; } 35% { transform: translateY(-9px); } "
    "70% { transform: scale(1.02, 0.97); }",
    "m-ombre": "0%, 100% { transform: none; } 35% { transform: scale(0.75); }",
    "m-regard": "0%, 100% { transform: none; } 15%, 40% { transform: translateX(-3.5px); } "
    "55%, 85% { transform: translateX(3.5px); }",
    "m-penche": "0%, 100% { transform: none; } 15%, 40% { transform: rotate(-4deg); } "
    "55%, 85% { transform: rotate(4deg); }",
    "m-surgit": "0% { opacity: 0; transform: translateY(6px) scale(0.4); } "
    "60% { opacity: 1; transform: translateY(-2px) scale(1.1); } "
    "100% { opacity: 1; transform: none; }",
    "m-cherche": "0%, 100% { transform: none; } 25% { transform: translateX(-3.5px); } "
    "75% { transform: translateX(3.5px); }",
    "m-penche-doux": "0%, 100% { transform: none; } 50% { transform: rotate(-5deg); }",
    "m-point": "0% { opacity: 0.2; } 35% { opacity: 1; } 100% { opacity: 1; }",
    "m-souffle": "0%, 100% { transform: none; } 50% { transform: scale(1, 1.015); }",
}

# Context -> (pose, motion rules: each one `animation` shorthand, or two for the eyes).
CONTEXTES: dict[str, tuple[str, tuple[str, ...]]] = {
    "accueil": (
        "",
        (
            ".m-bras { animation: m-lever 0.5s ease-out 0.2s 1 both; }",
            ".m-onde-1 { animation: m-onde 1s ease-out 0.7s 3 both; }",
            ".m-onde-2 { animation: m-onde 1s ease-out 0.85s 3 both; }",
            ".m-onde-3 { animation: m-onde 1s ease-out 1s 3 both; }",
            ".m-yeux { animation: m-cligne 0.3s ease-in-out 4.2s 1; }",
        ),
    ),
    "vigiking": (
        "",
        (
            ".m-corps { animation: m-saut 0.6s ease-out 0.2s 2 both; }",
            ".m-ombre { animation: m-ombre 0.6s ease-out 0.2s 2 both; }",
            ".m-onde-1 { animation: m-onde 1s ease-out 1.5s 2 both; }",
            ".m-onde-2 { animation: m-onde 1s ease-out 1.65s 2 both; }",
            ".m-onde-3 { animation: m-onde 1s ease-out 1.8s 2 both; }",
            ".m-yeux { animation: m-cligne 0.3s ease-in-out 4s 1; }",
        ),
    ),
    "404": (
        POSE_CALME,
        (
            ".m-yeux { animation: m-regard 2.4s ease-in-out 0.3s 1 both; }",
            ".m-tete { animation: m-penche 2.4s ease-in-out 0.3s 1 both; }",
            ".m-extra { animation: m-surgit 0.6s ease-out 2.6s 1 both; }",
        ),
    ),
    "recherche": (
        POSE_CALME,
        (
            (
                ".m-yeux { animation: m-cherche 1.4s ease-in-out 0.2s 2 both, "
                "m-cligne 0.3s ease-in-out 3.3s 1; }"
            ),
            ".m-tete { animation: m-penche-doux 2.8s ease-in-out 0.2s 1 both; }",
        ),
    ),
    "attente": (
        POSE_CALME,
        (
            ".m-point-1 { animation: m-point 1.2s ease-in-out 0.3s 3 both; }",
            ".m-point-2 { animation: m-point 1.2s ease-in-out 0.5s 3 both; }",
            ".m-point-3 { animation: m-point 1.2s ease-in-out 0.7s 3 both; }",
            ".m-corps { animation: m-souffle 2s ease-in-out 0.3s 2 both; }",
            (
                ".m-yeux { animation: m-cligne 0.3s ease-in-out 1.6s 1, "
                "m-cligne 0.3s ease-in-out 3.9s 1; }"
            ),
        ),
    ),
}

# The mouth, once the horn has left the lips (drawn on the beard, under the horn).
_TRAIT = {"fill": "none", "stroke": INK, "stroke-width": "2.5"}
BOUCHES = {
    "404": (
        "ellipse",
        {"cx": "120", "cy": "126.5", "rx": "3", "ry": "3.6", "fill": INK},
    ),
    "recherche": (
        "path",
        {"d": "M113.5 126.5 Q116.75 124 120 126.5 T126.5 126.5", **_TRAIT},
    ),
    "attente": ("path", {"d": "M114 125 Q120 129.5 126 125", **_TRAIT}),
}

# A question mark (404) and three dots (attente), each with its white sticker edge.
_INTERROGATION = (
    "M171 40 Q171 30 180 30 Q189 30 189 39 Q189 45 182.5 48.5 Q180 50 180 56"
)


def q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def _el(tag: str, attrs: dict[str, str]) -> ET.Element:
    return ET.Element(q(tag), attrs)


def _chemin(el: ET.Element, debut: str) -> bool:
    return el.tag == q("path") and (el.get("d") or "").startswith(debut)


def _cercle(el: ET.Element, cx: str) -> bool:
    return el.tag == q("circle") and el.get("cx") == cx


def _contient_cercle(el: ET.Element, cx: str, cy: str | None = None) -> bool:
    return el.tag == q("g") and any(
        _cercle(c, cx) and cy in (None, c.get("cy")) for c in el
    )


def envelopper(
    parent: ET.Element, membres: list[ET.Element], classe: str
) -> ET.Element:
    """Move `membres` (children of `parent`, in order) into a new <g class> in their place."""
    assert membres, classe
    g = _el("g", {"class": classe})
    parent.insert(list(parent).index(membres[0]), g)
    for m in membres:
        parent.remove(m)
        g.append(m)
    return g


def charger() -> ET.Element:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.fromstring(SOURCE.read_text(encoding="utf-8"), parser=parser)


def _grouper(root: ET.Element) -> None:
    """Group the parts that move, in the drawing and in its white edge alike."""
    halo = next(c for c in root if c.tag == q("g") and c.get("stroke-width") == "13")
    envelopper(halo, [c for c in halo if _chemin(c, "M82 92") or _chemin(c, "M90 88")
                      or _chemin(c, "M90 104") or (c.tag == q("rect") and c.get("x") == "81")
                      or _cercle(c, "89") or _cercle(c, "151")], "m-tete")  # fmt: skip
    envelopper(halo, [c for c in halo if _chemin(c, "M96.9 138") or _chemin(c, "M114 125")
                      or c.tag == q("ellipse") or _cercle(c, "74")], "m-bras")  # fmt: skip
    ondes_halo = next(c for c in halo if c.get("stroke-width") == "15.5")
    ondes = next(c for c in root if c.tag == q("g") and c.get("stroke") == "#19a6e3")
    for groupe in (ondes_halo, ondes):
        for i, arc in enumerate(list(groupe), start=1):
            envelopper(groupe, [arc], f"m-onde m-onde-{i}")

    enfants = list(root)
    debut = next(i for i, c in enumerate(enfants) if _contient_cercle(c, "89"))
    fin = next(i for i, c in enumerate(enfants) if _contient_cercle(c, "105.5"))
    tete = envelopper(root, enfants[debut : fin + 1], "m-tete")
    # The pupils (y 103) and their highlights, not the helmet's rivets (one is also at x 104).
    yeux = [
        c
        for c in tete
        if _contient_cercle(c, "104", "103") or _contient_cercle(c, "105.5", "101.5")
    ]
    envelopper(tete, yeux, "m-yeux")
    enfants = list(root)
    bras = next(i for i, c in enumerate(enfants)
                if c.tag is ET.Comment and "Arm raised" in (c.text or ""))  # fmt: skip
    envelopper(root, enfants[bras + 1 :], "m-bras")


def _taire(root: ET.Element) -> None:
    """No waves: the horn is silent."""
    halo = next(c for c in root if c.tag == q("g") and c.get("stroke-width") == "13")
    halo.remove(next(c for c in halo if c.get("stroke-width") == "15.5"))
    root.remove(
        next(c for c in root if c.tag == q("g") and c.get("stroke") == "#19a6e3")
    )
    root.remove(
        next(c for c in root if c.tag is ET.Comment and "The alert" in (c.text or ""))
    )


def _bouche(root: ET.Element, contexte: str) -> None:
    tete = next(c for c in root if c.get("class") == "m-tete")
    barbe = next(c for c in tete if _chemin(c, "M90 104") and c.get("fill") == "none")
    tag, attrs = BOUCHES[contexte]
    tete.insert(list(tete).index(barbe) + 1, _el(tag, attrs))


def _extra(contexte: str) -> ET.Element | None:
    if contexte == "404":
        g = _el("g", {"class": "m-extra"})
        trait = {"d": _INTERROGATION, "fill": "none", "stroke-linecap": "round"}
        g.append(_el("path", {**trait, "stroke": WHITE, "stroke-width": "14.5"}))
        g.append(_el("circle", {"cx": "180", "cy": "66", "r": "7.7", "fill": WHITE}))
        g.append(_el("path", {**trait, "stroke": INK, "stroke-width": "5.5"}))
        g.append(_el("circle", {"cx": "180", "cy": "66", "r": "3.4", "fill": INK}))
        return g
    if contexte == "attente":
        g = _el("g", {"class": "m-extra"})
        for i, x in enumerate(("170", "182", "194"), start=1):
            point = _el("g", {"class": f"m-point m-point-{i}"})
            point.append(
                _el("circle", {"cx": x, "cy": "62", "r": "7.7", "fill": WHITE})
            )
            point.append(_el("circle", {"cx": x, "cy": "62", "r": "3.4", "fill": INK}))
            g.append(point)
        return g
    return None


def _css(contexte: str) -> str:
    pose, mouvement = CONTEXTES[contexte]
    texte = " ".join(mouvement)
    noms = [n for n in KEYFRAMES if f"{n} " in texte]
    images = "".join(f"  @keyframes {n} {{ {KEYFRAMES[n]} }}\n" for n in noms)
    regles = "".join(f"  {regle}\n" for regle in mouvement)
    return (
        BASE_CSS
        + pose
        + "@media (prefers-reduced-motion: no-preference) {\n"
        + regles
        + images
        + "}\n"
    )


def variante(contexte: str) -> str:
    """The SVG of the mascot for `contexte`."""
    root = copy.deepcopy(charger())
    nom = f"mascotte-{contexte}"
    note = next(c for c in root if c.tag is ET.Comment)
    note.text = (
        f" Generated by tools/design/make_mascotte.py from assets/img/mascotte.svg, context "
        f"« {contexte} » (docs/mascotte/README.md): edit the drawing or the script, not this file. "
    )
    _grouper(root)
    if contexte not in ("accueil", "vigiking"):
        _taire(root)
        _bouche(root, contexte)
    ombre = next(c for c in root if c.tag == q("ellipse") and c.get("cx") == "122")
    ombre.set("class", "m-ombre")
    root.remove(ombre)
    defs = next(c for c in root if c.tag == q("defs"))
    root.insert(list(root).index(defs) + 1, ombre)
    corps = envelopper(root, list(root)[list(root).index(ombre) + 1 :], "m-corps")
    if (extra := _extra(contexte)) is not None:
        corps.append(extra)
    style = _el("style", {})
    style.text = _css(contexte)
    root.insert(list(root).index(note) + 1, style)
    ET.indent(root, space="  ")
    texte = ET.tostring(root, encoding="unicode")
    texte = texte.replace('id="mascotte-', f'id="{nom}-').replace(
        "url(#mascotte-", f"url(#{nom}-"
    )
    return texte + "\n"


def variantes() -> dict[str, str]:
    return {f"mascotte-{c}": variante(c) for c in CONTEXTES}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    attendus = variantes()
    for ancien in OUT.glob("*.svg"):
        if ancien.stem not in attendus:
            ancien.unlink()
    for nom, texte in attendus.items():
        (OUT / f"{nom}.svg").write_text(texte, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} : {', '.join(attendus)}.")


if __name__ == "__main__":
    main()
