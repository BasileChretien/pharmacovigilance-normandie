"""The mascot's animated variants, one per context (tools/design/make_mascotte.py).

Each variant is assets/img/mascotte.svg with a pose and a short animation of its own. Placed
as an <img>, it cannot be paused from the page: so every animation stops by itself within
5 seconds (WCAG 2.2.2 then asks for no pause button), and none plays when the reader asked
for reduced motion.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import make_mascotte as mm
from check_contrast import parse_scss_tokens

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "assets" / "img" / "mascotte"
CONTEXTES = {
    "accueil",
    "vigiking",
    "404",
    "recherche",
    "attente",
    "comprendre",
    "bon-usage",
    "normandie",
    "crpv",
    "actualites",
    "question",
    "medicaments",
    "sobre",
}
# The horn sounds (its waves show) only where the mascot announces something.
ALERTE = {"mascotte-accueil", "mascotte-vigiking", "mascotte-actualites"}
# What a variant shown beside risks, dosages or serious harm may do: blink, breathe, nod,
# look, lift its shield, raise the horn and sound it once. No hop, no rocking, nothing
# popping up.
MOUVEMENTS_DOUX = {
    "m-cligne",
    "m-souffle",
    "m-hoche",
    "m-presente",
    "m-cherche",
    "m-penche-doux",
    "m-lever",
    "m-onde",
}
MAX_SECONDES = 5.0

_MOTION_OK = re.compile(r"@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{")
_TIME = re.compile(r"(?<![\w.])(\d*\.?\d+)(ms|s)\b")


def fichiers() -> dict[str, str]:
    return {
        p.stem: p.read_text(encoding="utf-8") for p in sorted(DOSSIER.glob("*.svg"))
    }


def style(svg: str) -> str:
    match = re.search(r"<style>(.*?)</style>", svg, re.DOTALL)
    assert match, "pas de <style>"
    return match.group(1)


def sans_mouvement_permis(css: str) -> str:
    """The CSS without its @media (prefers-reduced-motion: no-preference) blocks."""
    out, pos = [], 0
    for match in _MOTION_OK.finditer(css):
        if match.start() < pos:
            continue
        out.append(css[pos : match.start()])
        depth, i = 1, match.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        pos = i
    out.append(css[pos:])
    return "".join(out)


def _sans_fonctions(animation: str) -> str:
    return re.sub(r"\w[\w-]*\([^)]*\)", " ", animation)  # cubic-bezier(…), steps(…)


def repetitions(animation: str) -> float:
    """How many times one `animation` shorthand value plays."""
    plain = _sans_fonctions(animation)
    assert "infinite" not in plain, animation
    rest = _TIME.sub(" ", plain)
    counts = [float(t) for t in rest.split() if re.fullmatch(r"\d*\.?\d+", t)]
    return counts[0] if counts else 1.0


def duree(animation: str) -> float:
    """Seconds until one `animation` shorthand value has played out."""
    plain = _sans_fonctions(animation)
    times = [
        float(v) / (1000 if unit == "ms" else 1) for v, unit in _TIME.findall(plain)
    ]
    assert times, animation
    delay = times[1] if len(times) > 1 else 0.0
    return delay + times[0] * repetitions(animation)


def test_one_variant_per_context_each_regenerated_from_the_drawing():
    attendu = mm.variantes()
    assert set(attendu) == {f"mascotte-{c}" for c in CONTEXTES}
    assert fichiers() == attendu, "lancer : uv run python tools/design/make_mascotte.py"


def test_variants_keep_the_theme_tokens_the_size_and_no_script():
    jetons = set(
        parse_scss_tokens(
            (ROOT / "assets" / "theme.scss").read_text(encoding="utf-8")
        ).values()
    )
    for nom, svg in fichiers().items():
        couleurs = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", svg)}
        assert couleurs <= jetons, f"{nom} : {sorted(couleurs - jetons)}"
        assert 'viewBox="0 0 240 280" width="240" height="280"' in svg
        assert "<script" not in svg and not re.search(r"\son\w+\s*=", svg), nom
        for ident in re.findall(r'\sid="([^"]+)"', svg):
            assert ident.startswith(f"{nom}-"), f"{nom} : id {ident}"


def test_nothing_moves_when_motion_is_reduced():
    for nom, svg in fichiers().items():
        reste = sans_mouvement_permis(style(svg))
        assert not re.search(r"\b(animation|transition)\s*:", reste), nom
        assert re.search(r"\banimation\s*:", style(svg)), f"{nom} : aucune animation"


def test_every_animation_stops_by_itself_within_five_seconds():
    for nom, svg in fichiers().items():
        for valeur in re.findall(r"\banimation\s*:\s*([^;}]+)", style(svg)):
            for une in valeur.split(","):
                assert duree(une) <= MAX_SECONDES, f"{nom} : {une.strip()}"


def test_the_duration_reader():
    assert duree("m-onde 1s ease-out 0.7s 3 both") == 3.7
    assert duree("m-saut 600ms cubic-bezier(.3,.7,.4,1) 0.2s 2 both") == 1.4
    assert duree("m-cligne 0.25s") == 0.25
    assert repetitions("m-onde 1s ease-out 0.7s 3 both") == 3
    assert repetitions("m-cligne 0.25s") == 1


def test_the_variants_of_serious_pages_stay_gentle():
    """Medicine sheets, alerts and serious harm (tests/test_mascotte.py SERIEUX) take one of
    these variants: gentle motions only, and the horn sounds once at most."""
    assert mm.DOUX <= CONTEXTES
    for contexte in mm.DOUX:
        css = style(fichiers()[f"mascotte-{contexte}"])
        noms = set(re.findall(r"@keyframes\s+([\w-]+)", css))
        assert noms <= MOUVEMENTS_DOUX, f"{contexte} : {sorted(noms - MOUVEMENTS_DOUX)}"
        for valeur in re.findall(r"\banimation\s*:\s*([^;}]+)", css):
            for une in valeur.split(","):
                if une.split()[0] == "m-onde":
                    assert repetitions(une) == 1, f"{contexte} : {une.strip()}"


def test_each_quiet_variant_has_a_mouth():
    """Once the horn leaves his lips, the face needs a mouth."""
    for nom, svg in fichiers().items():
        if nom not in ALERTE:
            assert 'class="m-bouche"' in svg, nom


def test_only_the_eyes_blink_and_look_around():
    """The eye group holds the pupils (y 103) and their highlights (y 101.5), nothing else:
    the helmet's rivets (y 86.5) would slide onto the face with every blink."""
    for nom, svg in fichiers().items():
        racine = ET.fromstring(svg)
        groupes = racine.findall(".//{http://www.w3.org/2000/svg}g[@class='m-yeux']")
        assert len(groupes) == 1, nom
        hauteurs = {
            c.get("cy") for c in groupes[0].iter("{http://www.w3.org/2000/svg}circle")
        }
        assert hauteurs == {"103", "101.5"}, f"{nom} : {sorted(hauteurs)}"


def test_the_horn_sounds_only_where_the_mascot_announces_something():
    for nom, svg in fichiers().items():
        assert ('class="m-onde' in svg) == (nom in ALERTE), nom
