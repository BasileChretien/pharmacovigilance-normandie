"""Build the Word template of the Vigiking bulletin: bulletin/word/modele-vigiking.docx.

pandoc writes modele.md to Word, which creates the bulletin's styles ("Encadré",
"Contre-indication"…, see word-vers-vigiking.lua); this script then gives each style the
look it has in the bulletin, so that authors see in Word roughly what they will get.

Usage: python bulletin/word/faire_modele.py
"""

from __future__ import annotations

import re
import subprocess
import zipfile
from pathlib import Path

from importer import commande_pandoc

ICI = Path(__file__).resolve().parent
SOURCE = ICI / "modele.md"
MODELE = ICI / "modele-vigiking.docx"

BORDURE = "".join(
    f'<w:{cote} w:val="single" w:sz="8" w:space="4" w:color="2F5597"/>'
    for cote in ("top", "left", "bottom", "right")
)
# Style name -> (paragraph properties, run properties), as in typst-template.typ.
LOOKS = {
    "Encadré": (
        f'<w:pBdr>{BORDURE}</w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="EEF3FA"/>',
        "",
    ),
    "Légende": ("", '<w:i/><w:sz w:val="20"/>'),
    "Références": ("", '<w:sz w:val="18"/>'),
    "Catégorie rouge": (
        '<w:shd w:val="clear" w:color="auto" w:fill="B03A2E"/>',
        '<w:b/><w:color w:val="FFFFFF"/>',
    ),
    "Catégorie verte": (
        '<w:shd w:val="clear" w:color="auto" w:fill="2E7D32"/>',
        '<w:b/><w:color w:val="FFFFFF"/>',
    ),
    "Catégorie bleue": (
        '<w:shd w:val="clear" w:color="auto" w:fill="2F5597"/>',
        '<w:b/><w:color w:val="FFFFFF"/>',
    ),
    "Catégorie jaune": (
        '<w:shd w:val="clear" w:color="auto" w:fill="F2C94C"/>',
        '<w:b/><w:color w:val="1F2937"/>',
    ),
    "Contre-indication": ("", '<w:b/><w:color w:val="C00000"/>'),
    "CredibleMeds": ("", '<w:i/><w:color w:val="B45309"/>'),
}


def styler(styles_xml: str) -> str:
    """Add each bulletin style's look to Word's styles.xml (pandoc leaves them plain)."""
    for nom, (paragraphe, caracteres) in LOOKS.items():
        motif = re.compile(
            r'(<w:style [^>]*><w:name w:val="'
            + re.escape(nom)
            + r'"\s*/>.*?)(</w:style>)',
            re.DOTALL,
        )
        ajout = (f"<w:pPr>{paragraphe}</w:pPr>" if paragraphe else "") + (
            f"<w:rPr>{caracteres}</w:rPr>" if caracteres else ""
        )
        styles_xml, n = motif.subn(
            lambda m, ajout=ajout: m.group(1) + ajout + m.group(2), styles_xml, count=1
        )
        if n != 1:
            raise SystemExit(f"faire_modele : style « {nom} » absent de {SOURCE.name}.")
    return styles_xml


def main() -> int:
    brut = MODELE.with_suffix(".tmp.docx")
    subprocess.run([*commande_pandoc(), str(SOURCE), "-o", str(brut)], check=True)
    with (
        zipfile.ZipFile(brut) as entree,
        zipfile.ZipFile(MODELE, "w", zipfile.ZIP_DEFLATED) as sortie,
    ):
        for info in entree.infolist():
            data = entree.read(info.filename)
            if info.filename == "word/styles.xml":
                data = styler(data.decode("utf-8")).encode("utf-8")
            sortie.writestr(info, data)
    brut.unlink()
    print(f"{MODELE.relative_to(ICI.parents[1])} écrit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
