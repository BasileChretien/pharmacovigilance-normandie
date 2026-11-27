"""Convert a Vigiking issue written in Word into the bulletin's text file.

The issue is written from the Word template (bulletin/word/modele-vigiking.docx: its
styles are the bulletin's building blocks, see word-vers-vigiking.lua). This script
writes bulletin/numeros/<AAAA-MM>/vigiking-<AAAA-MM>.qmd and its pictures; then
`quarto render` in bulletin/ makes the PDF and the web page.

The logos, the Vigiking banner and the standard back cover come from bulletin/commun/
(logo-rouen.png, logo-caen.png, bandeau.png, dos.md) when they are there; that folder
stays local, as the issues do.

Usage: python bulletin/word/importer.py numero.docx 2025-10 [--remplacer]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

BULLETIN = Path(__file__).resolve().parents[1]
FILTRE = BULLETIN / "word" / "word-vers-vigiking.lua"
# Front matter key, file in bulletin/commun/.
IMAGES_COMMUNES = {
    "logo-gauche": "logo-rouen.png",
    "logo-droite": "logo-caen.png",
    "bandeau": "bandeau.png",
}


def commande_pandoc() -> list[str]:
    """Quarto's own pandoc, else a pandoc on the PATH."""
    quarto = shutil.which("quarto")
    if quarto:
        return [quarto, "pandoc"]
    pandoc = shutil.which("pandoc")
    if pandoc:
        return [pandoc]
    raise SystemExit(
        "importer : installez Quarto (https://quarto.org), qui fournit pandoc."
    )


def importer(
    docx: Path, mois: str, bulletin: Path = BULLETIN, remplacer: bool = False
) -> Path:
    """Write the issue of month AAAA-MM from a Word file; return the .qmd written."""
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", mois):
        raise SystemExit(f"importer : « {mois} » n'est pas un mois AAAA-MM.")
    if not docx.is_file():
        raise SystemExit(f"importer : fichier introuvable : {docx}")
    nom = f"vigiking-{mois}"
    dossier = bulletin / "numeros" / mois
    sortie = dossier / f"{nom}.qmd"
    if sortie.exists() and not remplacer:
        raise SystemExit(
            f"importer : {sortie} existe déjà ; ajoutez --remplacer pour l'écraser."
        )
    (dossier / "images").mkdir(parents=True, exist_ok=True)
    meta = ["-M", f"fichier={nom}", "-M", "dossier-images=images"]
    commun = bulletin / "commun"
    for cle, fichier in IMAGES_COMMUNES.items():
        if (commun / fichier).is_file():
            # Copied next to the issue: Typst reads no file above the issue's folder.
            shutil.copyfile(commun / fichier, dossier / "images" / fichier)
            meta += ["-M", f"{cle}=images/{fichier}"]
    if (commun / "dos.md").is_file():
        meta += ["-M", "dos=../../commun/dos.md"]
    subprocess.run(
        [
            *commande_pandoc(),
            str(docx.resolve()),
            "--from=docx+styles",
            "--to=markdown-simple_tables-multiline_tables-grid_tables",
            "--standalone",
            "--wrap=none",
            f"--lua-filter={FILTRE}",
            "--extract-media=images",
            f"--output={sortie.name}",
            *meta,
        ],
        cwd=dossier,
        check=True,
    )
    return sortie


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("docx", type=Path, help="le numéro écrit dans Word")
    parser.add_argument("mois", help="le mois du numéro, AAAA-MM")
    parser.add_argument(
        "--remplacer", action="store_true", help="écraser le numéro existant"
    )
    args = parser.parse_args()
    sortie = importer(args.docx, args.mois, remplacer=args.remplacer)
    print(
        f"{sortie} écrit ; puis, dans bulletin/ : quarto render {sortie.relative_to(BULLETIN).as_posix()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
