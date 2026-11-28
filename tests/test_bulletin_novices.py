"""What colleagues who are not at ease with computers actually do (user tests of
28/11/2026): wrong files, abbreviated months, author lines typed their way, references
without brackets, a PDF left open… The tool must accept the common variants and, for the
rest, say in plain French what to do."""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bulletin"))
sys.path.insert(0, str(ROOT / "bulletin" / "word"))

import fabriquer
import importer as imp
import references
import verifier as ver
from verifier import Alerte

avec_pandoc = pytest.mark.skipif(
    shutil.which("quarto") is None and shutil.which("pandoc") is None,
    reason="needs pandoc (Quarto's)",
)


# --- The month ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texte", "mois"),
    [
        ("juil. 2099", "2099-07"),
        ("Oct 2025", "2025-10"),
        ("Sept. 2024", "2024-09"),
        ("10/2099", "2099-10"),
        ("Juillet-août 2018", "2018-07"),
        ("Février 2026", "2026-02"),
    ],
)
def test_shortened_and_numeric_months_are_read(texte, mois):
    assert fabriquer.lire_mois(texte) == mois


def test_a_subtitle_without_a_month_is_quoted_back(monkeypatch, tmp_path):
    monkeypatch.setattr(fabriquer, "sous_titre", lambda docx: "Numéro spécial")
    with pytest.raises(fabriquer.Echec, match="« Numéro spécial »"):
        fabriquer.mois_du_numero(tmp_path / "Vigiking mai 2099.docx", None)


# --- The dropped file -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("nom", "contenu", "attendu"),
    [
        ("numero.doc", b"x", "ancien format de Word"),
        ("numero.pdf", b"%PDF", "C'est un PDF"),
        ("~$mero.docx", b"x", "fichier temporaire de Word"),
        ("renomme.docx", b"pas un zip", "n'est pas un document Word lisible"),
        ("photo.png", b"x", "Déposez le fichier Word"),
    ],
)
def test_a_wrong_file_gets_a_plain_message(tmp_path, nom, contenu, attendu):
    (tmp_path / nom).write_bytes(contenu)
    with pytest.raises(fabriquer.Echec, match=attendu):
        fabriquer.verifier_entree(tmp_path / nom)


def test_a_document_still_open_in_word_is_noticed(tmp_path):
    docx = tmp_path / "Vigiking octobre.docx"
    docx.write_bytes(b"")
    assert not fabriquer.ouvert_dans_word(docx)
    (tmp_path / "~$giking octobre.docx").write_bytes(b"")
    assert fabriquer.ouvert_dans_word(docx)


# --- After the build ------------------------------------------------------------------


def test_a_failed_build_renames_the_previous_files(tmp_path):
    for f in fabriquer.produits(tmp_path, "vigiking-2099-08"):
        f.write_text("ancien", encoding="utf-8")
    note = fabriquer.ecarter_anciens(tmp_path, "vigiking-2099-08")
    assert "ancienne version" in note
    assert (tmp_path / "vigiking-2099-08 (ancienne version).pdf").is_file()
    assert not (tmp_path / "vigiking-2099-08.pdf").exists()


def test_the_verdict_says_whether_to_send():
    c, v = Alerte("corriger", "x"), Alerte("verifier", "y")
    assert fabriquer.verdict([c, v], "n.pdf", "n - à vérifier.txt").startswith(
        "✖ À ne pas envoyer encore : 1 point à corriger"
    )
    assert "regardez le 1 point" in fabriquer.verdict([v], "n.pdf", "l.txt")
    assert (
        fabriquer.verdict([], "n.pdf", "l.txt")
        == "✔ Prêt à envoyer : joignez « n.pdf » au courriel."
    )


def test_a_pdf_left_open_gets_a_plain_message(tmp_path):
    erreur = PermissionError(
        13, "Permission denied", str(tmp_path / "vigiking-2099-08.pdf")
    )
    message = fabriquer.message_d_erreur(erreur, tmp_path)
    assert message.startswith(
        "Le fichier « vigiking-2099-08.pdf » est ouvert dans un autre programme"
    )


def test_an_unexpected_error_leaves_its_detail_in_a_log(tmp_path):
    message = fabriquer.message_d_erreur(ValueError("boum"), tmp_path)
    assert message.startswith("Un problème inattendu est survenu ; rien n'est abîmé.")
    assert "boum" in (tmp_path / fabriquer.JOURNAL).read_text(encoding="utf-8")
    assert (
        fabriquer.message_d_erreur(SystemExit("importer : un message"), tmp_path)
        == "un message"
    )


# --- References typed without brackets ------------------------------------------------


def _pubmed(url: str) -> dict:
    resume = {"authors": [{"name": "Roden DM"}], "title": "Titre.", "source": "N Engl J Med",
              "pubdate": "2004", "volume": "350", "issue": "10", "pages": "1013-22", "articleids": []}  # fmt: skip
    return {"result": {"uids": ["14999113"], "14999113": resume}}


def test_a_pmid_in_parentheses_is_numbered(tmp_path):
    texte, alertes = references.resoudre(
        "Texte (PMID 14999113).\n", tmp_path / "c.json", _pubmed
    )
    assert texte.startswith("Texte^1^.") and alertes == []


def test_an_identifier_outside_brackets_is_flagged_but_not_in_a_reference_list(
    tmp_path,
):
    texte = "Voir PMID:12345678 et doi: 10.1136/abc-1.\n\n::: references\n1. A. doi:10.1056/X\n:::\n"
    _, alertes = references.resoudre(texte, tmp_path / "c.json", _pubmed)
    assert alertes == [
        "« PMID:12345678 » n'est pas entre crochets : écrivez [PMID 12345678] pour que la référence soit numérotée.",
        "« doi: 10.1136/abc-1 » n'est pas entre crochets : écrivez [DOI 10.1136/abc-1] pour que la référence soit numérotée.",
    ]


# --- The issue check: author lines, rubrics -------------------------------------------


def _numero(tmp_path: Path, titre: str, corps: str = "Texte.") -> Path:
    qmd = tmp_path / "n.qmd"
    qmd.write_text(
        f"---\ntitle: T\n---\n\n## Article {{{titre}}}\n\n{corps}\n", encoding="utf-8"
    )
    return qmd


def _messages(qmd: Path) -> list[str]:
    return [a.message for a in ver.verifier_numero(qmd) if a.niveau != "info"]


def test_the_template_placeholder_author_must_be_replaced(tmp_path):
    alertes = ver.verifier_numero(_numero(tmp_path, 'auteur="Initiale. Nom"'))
    assert [
        (a.niveau, a.message.split(" : ")[1][:31])
        for a in alertes
        if a.niveau != "info"
    ] == [("corriger", "le nom de l'auteur est encore c")]


def test_a_title_line_left_in_the_text_is_flagged(tmp_path):
    (message,) = _messages(
        _numero(tmp_path, 'auteur="K. B."', "Rubrique : Littérature\n\nTexte.")
    )
    assert "la ligne « Rubrique : Littérature » s'affiche dans le texte" in message


def test_only_an_unusual_rubric_is_flagged(tmp_path):
    assert _messages(_numero(tmp_path, 'auteur="K. B." rubrique="Littérature"')) == []
    (message,) = _messages(_numero(tmp_path, 'auteur="K. B." rubrique="Pharmacologie"'))
    assert (
        "la rubrique « Pharmacologie » n'est pas une des trois habituelles" in message
    )


# --- The Word import ------------------------------------------------------------------


def _importer(tmp_path: Path, markdown: str, mois: str = "2099-05") -> str:
    (tmp_path / "n.md").write_text(markdown, encoding="utf-8")
    subprocess.run(
        [*imp.commande_pandoc(), "n.md", "-o", "n.docx"], cwd=tmp_path, check=True
    )
    return imp.importer(tmp_path / "n.docx", mois, bulletin=tmp_path / "b").read_text(
        encoding="utf-8"
    )


@avec_pandoc
def test_par_lines_rubric_variants_and_a_missing_subtitle(tmp_path):
    texte = _importer(tmp_path, (
        "---\ntitle: T\n---\n\n# Un\n\nPar K. Benali\n\nRubrique : Litterature\n\nTexte.\n\n"
        "# Deux\n\nAuteur : A. B.\n\nRubrique : cas d'ici\n\nTexte.\n\n"
        "# Trois\n\nPar ailleurs, le texte commence ainsi.\n"
    ))  # fmt: skip
    un, deux, trois = (l for l in texte.splitlines() if l.startswith("## "))
    assert 'auteur="K. Benali"' in un and 'rubrique="Littérature"' in un
    assert "rubrique=\"Cas d'ici et d'ailleurs\"" in deux
    assert "auteur" not in trois and "Par ailleurs, le texte commence ainsi." in texte
    assert "numero: Mai 2099" in texte  # no subtitle: the month given to the import


@avec_pandoc
def test_a_document_without_any_article_is_not_built(tmp_path, monkeypatch):
    (tmp_path / "n.md").write_text(
        "---\ntitle: Compte rendu\nsubtitle: Mai 2099\n---\n\nTexte.\n",
        encoding="utf-8",
    )
    subprocess.run(
        [*imp.commande_pandoc(), "n.md", "-o", "n.docx"], cwd=tmp_path, check=True
    )
    original = imp.importer
    monkeypatch.setattr(fabriquer.importer, "importer",
                        lambda docx, mois, remplacer: original(docx, mois, bulletin=tmp_path / "b", remplacer=True))  # fmt: skip
    with pytest.raises(fabriquer.Echec, match="aucun article"):
        fabriquer.preparer_word(tmp_path / "n.docx", None)
    assert zipfile.is_zipfile(tmp_path / "n.docx")
