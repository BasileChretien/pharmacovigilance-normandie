"""The bulletin's colours pass WCAG AA contrast, as the site's do (check_contrast.py).

The colours live in bulletin/_extensions/vigiking/typst-template.typ; the web version
(vigiking.css, vigiking.lua) repeats them and must not drift.
"""

import re
from pathlib import Path

import pytest
from check_contrast import contrast_ratio

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "bulletin" / "_extensions" / "vigiking"
AA = 4.5


def couleurs_typst() -> dict[str, str]:
    texte = (EXT / "typst-template.typ").read_text(encoding="utf-8")
    return dict(
        re.findall(r'^#let ([a-z-]+) = rgb\("(#[0-9a-f]{6})"\)', texte, re.MULTILINE)
    )


def melange(a: str, b: str, t: float) -> str:
    """sRGB mix, as typst-template.typ (teinte) and vigiking.lua do."""
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - t) + y * t):02x}" for x, y in zip(ca, cb))


C = couleurs_typst()
PAIRES = [
    ("encre", "#ffffff"),
    ("encre-douce", "#ffffff"),
    ("bleu", "#ffffff"),
    ("vert", "#ffffff"),
    ("rouge-ci", "#ffffff"),
    ("orange-cm", "#ffffff"),
    ("encre", "brume"),
    ("rouge-ci", "brume"),
    ("orange-cm", "brume"),
    ("#ffffff", "manche"),
    ("ecume", "manche"),
    ("#ffffff", "rouge-ci"),  # category labels
    ("#ffffff", "vert"),
    ("#ffffff", "bleu"),
    ("encre", "dore"),
]


@pytest.mark.parametrize(("texte", "fond"), PAIRES)
def test_each_text_and_background_pair_passes_aa(texte, fond):
    avant, arriere = C.get(texte, texte), C.get(fond, fond)
    assert contrast_ratio(avant, arriere) >= AA, (texte, fond)


def test_every_article_colour_between_blue_and_green_passes_aa():
    for k in range(21):
        teinte = melange(C["bleu"], C["vert"], k / 20)
        assert contrast_ratio(teinte, "#ffffff") >= AA, teinte
        assert contrast_ratio(teinte, C["brume"]) >= AA, teinte


def test_the_web_version_uses_the_same_colours():
    css = (EXT / "vigiking.css").read_text(encoding="utf-8")
    lua = (EXT / "vigiking.lua").read_text(encoding="utf-8")
    for nom in (
        "encre",
        "encre-douce",
        "brume",
        "manche",
        "ecume",
        "bleu",
        "vert",
        "rouge-ci",
        "orange-cm",
    ):
        assert f"--{nom}: {C[nom]};" in css, nom
    rgb = lambda h: (
        "{ " + ", ".join(str(int(h[i : i + 2], 16)) for i in (1, 3, 5)) + " }"
    )
    assert f"BLEU, VERT = {rgb(C['bleu'])}, {rgb(C['vert'])}" in lua
