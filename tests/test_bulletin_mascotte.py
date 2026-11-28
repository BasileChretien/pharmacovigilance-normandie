"""The site's mascot in the Vigiking PDF masthead (tools/design/make_bulletin_mascotte.py)."""

from pathlib import Path

import make_bulletin_mascotte as mbm
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "bulletin" / "_extensions" / "vigiking"


def test_the_partial_is_the_sites_mascot_regenerated():
    dessin = (ROOT / "assets" / "img" / "mascotte.svg").read_text(encoding="utf-8")
    assert (EXT / "mascotte.typ").read_text(encoding="utf-8") == mbm.typst(
        mbm.compact(dessin)
    )


def test_compact_drops_comments_and_line_breaks_but_keeps_the_drawing():
    svg = '<svg a="1">\n  <!-- une note -->\n  <path d="M0 0 L1 1"/>\n</svg>\n'
    assert mbm.compact(svg) == '<svg a="1"><path d="M0 0 L1 1"/></svg>'


def test_the_partial_escapes_the_svg_and_refuses_a_dollar():
    texte = mbm.typst('<svg a="1">\\</svg>')
    assert '#let mascotte-svg = bytes("<svg a=\\"1\\">\\\\</svg>")' in texte
    with pytest.raises(ValueError):
        mbm.typst("<svg>$</svg>")  # Pandoc would read it as a template variable


def test_the_template_puts_the_mascot_in_the_cover_masthead():
    assert "- mascotte.typ" in (EXT / "_extension.yml").read_text(encoding="utf-8")
    template = (EXT / "typst-template.typ").read_text(encoding="utf-8")
    assert "$mascotte.typ()$" in template
    une = template[template.index("#let une(") :]
    une = une[: une.index("\n#let ", 1)]
    assert 'image(mascotte-svg, format: "svg"' in une
    assert 'alt: ""' in une[une.index("mascotte-svg") :]  # decorative
