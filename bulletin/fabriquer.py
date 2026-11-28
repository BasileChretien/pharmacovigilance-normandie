"""Make a Vigiking issue in one step: from the Word file to the PDF, the web page and the
list of what to check.

Drop the Word file on « Fabriquer le Vigiking.bat » (or run this script with its path):

1. the month is read from the document's subtitle (« Octobre 2025 », « oct. 2025 »…);
2. the Word file is checked (verifier.py), imported (importer.py), and the references typed
   as a DOI or a PMID are found and numbered (references.py);
3. Quarto makes the PDF and the web page;
4. the checks list what to fix, in the window and in a text file;
5. the PDF, the web page and that list are copied next to the Word file; the PDF opens,
   and a last line says whether the issue can be sent.

Written for people who are not at ease with computers: every failure ends in a plain
French message saying what to do (the technical detail goes to a log next to the Word
file), and a failed build renames the previous PDF so that nobody sends it as new.

A Markdown issue (numeros/AAAA-MM/vigiking-AAAA-MM.qmd) can be given instead: it is
rendered and checked as it is.

Usage: python bulletin/fabriquer.py numero.docx [--mois AAAA-MM] [--sans-liens] [--sans-ouvrir]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

BULLETIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BULLETIN / "word"))

import importer
import references
import verifier
from verifier import Alerte

POLICES = BULLETIN / "_extensions" / "vigiking" / "fonts"
CACHE_REFERENCES = BULLETIN / ".cache" / "references.json"
JOURNAL = "Vigiking - journal technique.txt"
# Month names, full and shortened, without accents (« oct. 2025 », « juil. 2025 »).
NOMS_MOIS = {
    "janvier": 1, "janv": 1, "jan": 1, "fevrier": 2, "fevr": 2, "fev": 2, "mars": 3,
    "avril": 4, "avr": 4, "mai": 5, "juin": 6, "juillet": 7, "juil": 7, "aout": 8,
    "septembre": 9, "sept": 9, "sep": 9, "octobre": 10, "oct": 10, "novembre": 11,
    "nov": 11, "decembre": 12, "dec": 12,
}  # fmt: skip
_NOM = "|".join(sorted(NOMS_MOIS, key=len, reverse=True))
# « Juillet-août 2018 »: the first month.
MOIS_EN_LETTRES = re.compile(
    rf"\b({_NOM})\.?(?:\s*[-–/]\s*(?:{_NOM})\.?)?\s+(20\d{{2}})\b"
)
MOIS_ISO = re.compile(r"\b(20\d{2})-(0[1-9]|1[0-2])\b")
MOIS_EN_CHIFFRES = re.compile(r"\b(0?[1-9]|1[0-2])\s*[/.-]\s*(20\d{2})\b")
# Reference warnings that leave the bulletin wrong (raw text, "non trouvée"): to fix.
A_CORRIGER = ("introuvable", "connexion", "non comprise", "entre crochets")


class Echec(Exception):
    """A step failed: the message says what to do, in plain French."""


@dataclass(frozen=True)
class Resultat:
    rapport: str
    verdict: str
    dossier: Path
    fichiers: list[Path]


def sans_accents(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c)
    )


def lire_mois(texte: str) -> str | None:
    """« Octobre 2025 », « oct. 2025 », « 10/2025 » or « 2025-10 » → "2025-10"."""
    t = sans_accents(texte).lower()
    if trouve := MOIS_ISO.search(t):
        return f"{trouve[1]}-{trouve[2]}"
    if trouve := MOIS_EN_LETTRES.search(t):
        return f"{trouve[2]}-{NOMS_MOIS[trouve[1]]:02d}"
    if trouve := MOIS_EN_CHIFFRES.search(t):
        return f"{trouve[2]}-{int(trouve[1]):02d}"
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
    """The month: given, else from the subtitle, else (no subtitle) from the file name."""
    if impose:
        return impose
    texte = sous_titre(docx)
    if mois := lire_mois(texte):
        return mois
    if texte:
        raise Echec(
            f"Le sous-titre du document dit « {texte} » : le mois n'y est pas reconnu. "
            "Écrivez-le en toutes lettres avec l'année, par exemple « Octobre 2025 », "
            "puis déposez à nouveau le fichier."
        )
    if mois := lire_mois(docx.stem.replace("_", " ")):
        return mois
    raise Echec(
        "Le document n'a pas de sous-titre donnant le mois du numéro. Dans Word, écrivez "
        "le mois sous le titre, au style « Sous-titre » (par exemple « Octobre 2025 »), "
        "puis déposez à nouveau le fichier."
    )


def verifier_entree(source: Path) -> None:
    """The dropped file is a Word document that can be read, or say what to do."""
    nom, extension = source.name, source.suffix.lower()
    if not source.is_file():
        raise Echec(f"Le fichier « {nom} » est introuvable : déposez-le à nouveau.")
    if nom.startswith("~$"):
        raise Echec(
            "C'est un fichier temporaire de Word (son nom commence par ~$) : déposez le "
            "vrai document, celui dont le nom ne commence pas par ~$."
        )
    resave = (
        "Ouvrez-le dans Word, faites Fichier › Enregistrer sous › Document Word (*.docx), "
        "puis déposez ce nouveau fichier."
    )
    if extension == ".doc":
        raise Echec(f"Ce fichier est à l'ancien format de Word (.doc). {resave}")
    if extension == ".pdf":
        raise Echec(
            "C'est un PDF : déposez le fichier Word du numéro (.docx), pas le PDF."
        )
    if extension not in (".docx", ".qmd"):
        raise Echec("Déposez le fichier Word du numéro (.docx).")
    if extension == ".docx" and not zipfile.is_zipfile(source):
        raise Echec(
            f"Ce fichier n'est pas un document Word lisible, ou il est abîmé. {resave}"
        )


def ouvert_dans_word(docx: Path) -> bool:
    """Word keeps a lock file (« ~$ » and the name, its first letters cut) while it is open."""
    nom = docx.name
    return any((docx.parent / f"~${n}").exists() for n in {nom, nom[1:], nom[2:]})


def trouver_references(qmd: Path) -> list[Alerte]:
    """Number the [PMID …] / [DOI …] citations and write the list (references.py)."""
    texte = qmd.read_text(encoding="utf-8")
    nouveau, avertissements = references.resoudre(texte, CACHE_REFERENCES)
    if nouveau != texte:
        qmd.write_text(nouveau, encoding="utf-8")
    return [
        Alerte("corriger" if any(m in a.lower() for m in A_CORRIGER) else "verifier", a)
        for a in avertissements
    ]


def preparer_word(docx: Path, mois: str | None) -> tuple[Path, list[Alerte]]:
    """Steps 1-2: check and import the Word file, find its references."""
    print("1/4  Lecture du document Word…")
    alertes = verifier.verifier_docx(docx)
    if ouvert_dans_word(docx):
        alertes.append(Alerte("verifier", (
            "Le document est encore ouvert dans Word : si vous l'avez modifié sans "
            "l'enregistrer, ces modifications ne sont pas dans le PDF. Enregistrez-le, puis "
            "déposez-le à nouveau."
        )))  # fmt: skip
    qmd = importer.importer(docx, mois_du_numero(docx, mois), remplacer=True)
    if not re.search(r"(?m)^## ", qmd.read_text(encoding="utf-8")):
        raise Echec(
            "Ce document ne contient aucun article (aucun titre au style « Titre 1 ») : "
            "est-ce bien le fichier du bulletin ? Chaque article commence par un titre au "
            "style « Titre 1 »."
        )
    print("2/4  Références (DOI, PMID)…")
    return qmd, alertes + trouver_references(qmd)


def rendre(qmd: Path, dossier: Path) -> None:
    """Quarto makes the PDF and the web page; its log goes next to the Word file if it fails."""
    if shutil.which("quarto") is None:
        raise Echec(
            "L'installation n'est pas faite sur cet ordinateur : double-cliquez sur le "
            "fichier Installer, dans le dossier du bulletin, puis recommencez."
        )
    cible = qmd.relative_to(BULLETIN).as_posix()
    sortie = subprocess.run(
        ["quarto", "render", cible], cwd=BULLETIN, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )  # fmt: skip
    if sortie.returncode != 0:
        (dossier / JOURNAL).write_text(
            sortie.stdout + "\n" + sortie.stderr, encoding="utf-8"
        )
        raise Echec(
            f"La mise en page a échoué. Le détail technique est dans « {JOURNAL} », à côté "
            "du fichier Word : envoyez ce fichier à la personne qui gère le bulletin."
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


def verifier_numero(qmd: Path, avec_liens: bool, depuis_word: bool) -> list[Alerte]:
    alertes = verifier.verifier_numero(qmd, textes_alternatifs=not depuis_word)
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


def produits(dossier: Path, stem: str) -> list[Path]:
    """The PDF, the web page and the list, next to the Word file."""
    return [
        dossier / f"{stem}.pdf",
        dossier / f"{stem}.html",
        dossier / f"{stem} - à vérifier.txt",
    ]


def ecarter_anciens(dossier: Path, stem: str) -> str:
    """After a failed build, the previous one's files renamed « … (ancienne version) », so
    that nobody sends them as new; the sentence that says so."""
    restes, renommes = [], 0
    for f in produits(dossier, stem):
        if f.exists():
            try:
                os.replace(f, f.with_name(f"{f.stem} (ancienne version){f.suffix}"))
                renommes += 1
            except OSError:
                restes.append(f.name)
    if restes:
        return f"\n  Attention : « {restes[0]} », encore ouvert, n'est pas à jour : ne l'envoyez pas."
    if renommes:
        return "\n  Les fichiers de la fabrication précédente sont renommés « (ancienne version) » : ne les envoyez pas."
    return ""


def copier_a_cote(qmd: Path, dossier: Path, rapport: str) -> list[Path]:
    """The PDF, the web page (it links the PDF by name) and the list, next to the Word file."""
    sortie = BULLETIN / "_output" / qmd.parent.relative_to(BULLETIN)
    copies = []
    for extension in (".pdf", ".html"):
        source = sortie / qmd.with_suffix(extension).name
        if source.is_file():
            copies.append(Path(shutil.copy2(source, dossier / source.name)))
    liste = dossier / f"{qmd.stem} - à vérifier.txt"
    liste.write_text(rapport + "\n", encoding="utf-8")
    (dossier / JOURNAL).unlink(missing_ok=True)  # the log of an earlier failure
    return [*copies, liste]


def verdict(alertes: list[Alerte], pdf: str, liste: str) -> str:
    """The last line: can the issue be sent, and what to do."""
    corriger = sum(a.niveau == "corriger" for a in alertes)
    verifier_ = sum(a.niveau == "verifier" for a in alertes)
    if corriger:
        s = "s" * (corriger > 1)
        return (
            f"✖ À ne pas envoyer encore : {corriger} point{s} à corriger dans le fichier "
            f"Word. Envoyez « {liste} » à l'auteur, puis déposez ici sa version corrigée."
        )
    if verifier_:
        s = "s" * (verifier_ > 1)
        return (
            f"⚠ Presque prêt : regardez le{s} {verifier_} point{s} à vérifier ; s'il{s} "
            f"vous convien{'nent' if s else 't'}, joignez « {pdf} » au courriel."
        )
    return f"✔ Prêt à envoyer : joignez « {pdf} » au courriel."


def fabriquer(source: Path, mois: str | None, avec_liens: bool) -> Resultat:
    """Run every step; return the report, the verdict and the files made."""
    verifier_entree(source)
    depuis_word = source.suffix.lower() == ".docx"
    if depuis_word:
        qmd, alertes = preparer_word(source, mois)
    else:
        qmd, alertes = source.resolve(), []
    dossier = source.parent if depuis_word else qmd.parent
    try:
        print("3/4  Mise en page du PDF et de la page web (une à deux minutes)…")
        rendre(qmd, dossier)
        print("4/4  Vérifications…")
        alertes = sans_doublons(alertes + verifier_numero(qmd, avec_liens, depuis_word))
    except Exception as erreur:
        note = ecarter_anciens(dossier, qmd.stem) if depuis_word else ""
        if isinstance(erreur, Echec):
            raise Echec(str(erreur) + note) from erreur
        raise
    quand = dt.datetime.now().strftime("le %d/%m/%Y à %H:%M")
    titre = (
        f"Vigiking {qmd.stem.removeprefix('vigiking-')} : points à vérifier "
        f"(fichier « {source.name} », fabriqué {quand})"
    )
    rapport = verifier.rapport(alertes, titre)
    pdf, _, liste = produits(dossier, qmd.stem)
    fichiers = copier_a_cote(qmd, dossier, rapport)
    return Resultat(rapport, verdict(alertes, pdf.name, liste.name), dossier, fichiers)


def message_d_erreur(erreur: BaseException, dossier: Path) -> str:
    """Any failure, in plain French; an unexpected one leaves its detail in a log."""
    if isinstance(erreur, Echec):
        return str(erreur)
    if isinstance(erreur, SystemExit):  # importer.py, verifier.py: « module : message »
        return re.sub(r"^\w+ : ", "", str(erreur))
    if isinstance(erreur, PermissionError):
        nom = Path(erreur.filename).name if erreur.filename else "un des fichiers"
        return (
            f"Le fichier « {nom} » est ouvert dans un autre programme (lecteur de PDF, "
            "navigateur, Word). Fermez-le, puis déposez à nouveau le fichier Word."
        )
    journal = dossier / JOURNAL
    try:
        journal.write_text(
            "".join(traceback.format_exception(erreur)), encoding="utf-8"
        )
    except OSError:
        journal = None
    detail = (
        f"Le détail technique est dans « {JOURNAL} », à côté du fichier Word : "
        if journal
        else ""
    )
    notes = "".join(getattr(erreur, "__notes__", []))
    return (
        f"Un problème inattendu est survenu ; rien n'est abîmé. {detail}envoyez-le à la "
        f"personne qui gère le bulletin.{notes}"
    )


def afficher(resultat: Resultat, ouvert: bool) -> None:
    print("\n" + resultat.rapport + "\n")
    print(resultat.verdict)
    print(f"\nLes fichiers sont à côté du fichier Word, dans {resultat.dossier} :")
    roles = {
        ".pdf": "à joindre au courriel",
        ".html": "la page web, à garder",
        ".txt": "la liste à vérifier",
    }
    for f in resultat.fichiers:
        print(f"  • {f.name} ({roles.get(f.suffix, '')})")
    if ouvert:
        print("\nLe PDF vient de s'ouvrir.")
    print("Vous pouvez fermer cette fenêtre.")


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
        resultat = fabriquer(args.source, args.mois, not args.sans_liens)
    # Deliberately everything: whoever drops the file gets a French sentence, never a
    # traceback; an unexpected error's detail goes to the log (message_d_erreur).
    except (Exception, SystemExit) as erreur:  # noqa: BLE001
        print(f"\n✖ {message_d_erreur(erreur, args.source.parent)}")
        print("\nVous pouvez fermer cette fenêtre.")
        return 1
    pdf = next((f for f in resultat.fichiers if f.suffix == ".pdf"), None)
    ouvrir = bool(pdf) and not args.sans_ouvrir and hasattr(os, "startfile")
    if ouvrir:
        os.startfile(pdf)  # Windows: the PDF in the default viewer
    afficher(resultat, ouvrir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
