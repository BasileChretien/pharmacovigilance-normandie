"""Make a Vigiking issue in one step: from the Word file to the PDF, the web page and the
list of what to check.

Drop the Word file on « Fabriquer le Vigiking.bat » (or run this script with its path):

1. the month is read from the document's subtitle (« Octobre 2025 »);
2. the Word file is checked (verifier.py), imported (importer.py), and the references typed
   as a DOI or a PMID are found and numbered (references.py);
3. Quarto makes the PDF and the web page;
4. the checks list what to fix, in the window and in a text file;
5. the PDF, the web page and that list are copied next to the Word file; the PDF opens.

A Markdown issue (numeros/AAAA-MM/vigiking-AAAA-MM.qmd) can be given instead: it is
rendered and checked as it is.

Usage: python bulletin/fabriquer.py numero.docx [--mois AAAA-MM] [--sans-liens] [--sans-ouvrir]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

BULLETIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BULLETIN / "word"))

import importer
import references
import verifier
from verifier import Alerte

POLICES = BULLETIN / "_extensions" / "vigiking" / "fonts"
CACHE_REFERENCES = BULLETIN / ".cache" / "references.json"
MOIS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}  # fmt: skip


class Echec(Exception):
    """A step failed: the message says what to do, in plain French."""


def sans_accents(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c)
    )


def lire_mois(texte: str) -> str | None:
    """« Octobre 2025 », « octobre 2025 » or « 2025-10 » → "2025-10"."""
    t = sans_accents(texte).lower()
    trouve = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])\b", t)
    if trouve:
        return f"{trouve[1]}-{trouve[2]}"
    for nom, numero in MOIS.items():
        trouve = re.search(rf"\b{nom}\s+(20\d{{2}})\b", t)
        if trouve:
            return f"{trouve[1]}-{numero:02d}"
    return None


def sous_titre(docx: Path) -> str:
    """The Word document's subtitle (style « Sous-titre »), read by pandoc."""
    sortie = subprocess.run(
        [*importer.commande_pandoc(), str(docx), "--from=docx", "--to=markdown", "--standalone"],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )  # fmt: skip
    trouve = re.search(r"^subtitle:\s*(.+)$", sortie.stdout, flags=re.MULTILINE)
    return trouve[1].strip().strip("'\"") if trouve else ""


def mois_du_numero(docx: Path, impose: str | None) -> str:
    mois = (
        impose or lire_mois(sous_titre(docx)) or lire_mois(docx.stem.replace("_", " "))
    )
    if not mois:
        raise Echec(
            "Le mois du numéro est introuvable. Écrivez-le dans le sous-titre du document "
            "Word (style « Sous-titre »), par exemple « Octobre 2025 », puis recommencez."
        )
    return mois


def trouver_references(qmd: Path) -> list[Alerte]:
    """Number the [PMID …] / [DOI …] citations and write the list (references.py)."""
    texte = qmd.read_text(encoding="utf-8")
    nouveau, avertissements = references.resoudre(texte, CACHE_REFERENCES)
    if nouveau != texte:
        qmd.write_text(nouveau, encoding="utf-8")
    return [
        Alerte("corriger" if "introuvable" in a.lower() else "verifier", a)
        for a in avertissements
    ]


def rendre(qmd: Path) -> None:
    """Quarto makes the PDF and the web page; its log is kept if it fails."""
    if shutil.which("quarto") is None:
        raise Echec(
            "Quarto n'est pas installé sur cet ordinateur : lancez « Installer.bat » "
            "(dossier bulletin), puis recommencez."
        )
    cible = qmd.relative_to(BULLETIN).as_posix()
    sortie = subprocess.run(
        ["quarto", "render", cible], cwd=BULLETIN, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )  # fmt: skip
    if sortie.returncode != 0:
        journal = qmd.with_name("journal-quarto.txt")
        journal.write_text(sortie.stdout + "\n" + sortie.stderr, encoding="utf-8")
        raise Echec(
            "La mise en page a échoué. Le détail technique est dans "
            f"{journal} : envoyez ce fichier à la personne qui gère le bulletin."
        )


def mesures(qmd: Path) -> list[dict]:
    """Each article's text size and overflow, left in the PDF by the template."""
    typ = qmd.with_suffix(".typ")
    if not typ.is_file():
        return []
    sortie = subprocess.run(
        ["quarto", "typst", "eval", "query(<vigiking-mesure>).map(it => it.value)",
         "--in", typ.name, "--font-path", str(POLICES)],
        cwd=typ.parent, capture_output=True, check=False,
    )  # fmt: skip
    # Quarto passes Typst's answer on, on stdout or stderr depending on the version.
    for flux in (sortie.stdout, sortie.stderr):
        texte = flux.decode("utf-8", errors="replace").strip()
        if texte.startswith("["):
            try:
                return json.loads(texte.splitlines()[0])
            except json.JSONDecodeError:
                pass
    return []


def sans_doublons(alertes: list[Alerte]) -> list[Alerte]:
    """The Word file and the issue are both checked: one line per finding."""
    return list(dict.fromkeys(alertes))


def verifier_numero(qmd: Path, avec_liens: bool) -> list[Alerte]:
    alertes = verifier.verifier_numero(qmd)
    mesurees = mesures(qmd)
    if mesurees:
        alertes += verifier.verifier_mesures(mesurees)
    else:
        alertes.append(
            Alerte("info", "La taille du texte des articles n'a pas pu être relue.")
        )
    if avec_liens:
        alertes += verifier.verifier_liens(
            verifier.liens(qmd.read_text(encoding="utf-8"))
        )
    return alertes


def copier_a_cote(qmd: Path, dossier: Path, rapport: str) -> list[Path]:
    """The PDF, the web page (it links the PDF by name) and the list, next to the Word file."""
    produits = BULLETIN / "_output" / qmd.parent.relative_to(BULLETIN)
    copies = []
    for extension in (".pdf", ".html"):
        source = produits / qmd.with_suffix(extension).name
        if source.is_file():
            copies.append(Path(shutil.copy2(source, dossier / source.name)))
    liste = dossier / f"{qmd.stem} - à vérifier.txt"
    liste.write_text(rapport + "\n", encoding="utf-8")
    return [*copies, liste]


def fabriquer(
    source: Path, mois: str | None, avec_liens: bool
) -> tuple[str, list[Path]]:
    """Run every step; return the report and the files made."""
    alertes: list[Alerte] = []
    if source.suffix.lower() == ".docx":
        print("1/4  Lecture du document Word…")
        alertes += verifier.verifier_docx(source)
        mois = mois_du_numero(source, mois)
        qmd = importer.importer(source, mois, remplacer=True)
        print("2/4  Références (DOI, PMID)…")
        alertes += trouver_references(qmd)
    elif source.suffix.lower() == ".qmd":
        qmd = source.resolve()
    else:
        raise Echec("Déposez le fichier Word du numéro (.docx).")
    print("3/4  Mise en page du PDF et de la page web (une à deux minutes)…")
    rendre(qmd)
    print("4/4  Vérifications…")
    alertes += verifier_numero(qmd, avec_liens)
    titre = f"Vigiking {qmd.stem.removeprefix('vigiking-')} : points à vérifier"
    rapport = verifier.rapport(sans_doublons(alertes), titre)
    dossier = source.parent if source.suffix.lower() == ".docx" else qmd.parent
    return rapport, copier_a_cote(qmd, dossier, rapport)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "source", type=Path, help="le numéro : fichier Word (.docx) ou .qmd"
    )
    parser.add_argument(
        "--mois", help="le mois AAAA-MM, s'il n'est pas dans le sous-titre"
    )
    parser.add_argument(
        "--sans-liens", action="store_true", help="ne pas vérifier les liens"
    )
    parser.add_argument(
        "--sans-ouvrir", action="store_true", help="ne pas ouvrir le PDF"
    )
    args = parser.parse_args()
    try:
        rapport, fichiers = fabriquer(args.source, args.mois, not args.sans_liens)
    except (Echec, SystemExit) as erreur:
        print(f"\n✖ {erreur}")
        return 1
    print("\n" + rapport + "\n\nFichiers prêts :")
    for f in fichiers:
        print(f"  {f}")
    pdf = next((f for f in fichiers if f.suffix == ".pdf"), None)
    if pdf and not args.sans_ouvrir and hasattr(os, "startfile"):
        os.startfile(pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
