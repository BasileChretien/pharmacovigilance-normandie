"""Tests for bulletin/word/references.py: bracket citations become numbers and a list."""

import importlib.util
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "references", ROOT / "bulletin" / "word" / "references.py"
)
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)

KHATIB = {
    "DOI": "10.1136/postgradmedj-2020-138661",
    "title": ["Managing drug-induced QT prolongation in clinical practice"],
    "author": [
        {"given": "Rani", "family": "Khatib", "sequence": "first"},
        {"given": "Fatima R N", "family": "Sabir", "sequence": "additional"},
        {"given": "Caroline", "family": "Omari", "sequence": "additional"},
        {"given": "Chris", "family": "Pepper", "sequence": "additional"},
        {"given": "Muzahir H.", "family": "Tayebjee", "sequence": "additional"},
    ],
    "container-title": ["Postgraduate Medical Journal"],
    "short-container-title": ["Postgrad Med J"],
    "volume": "97",
    "issue": "1149",
    "page": "452-458",
    "published-print": {"date-parts": [[2021, 7]]},
    "published-online": {"date-parts": [[2020, 10, 29]]},
    "issued": {"date-parts": [[2020, 10, 29]]},
}
KHATIB_VANCOUVER = (
    "Khatib R, Sabir FRN, Omari C, Pepper C, Tayebjee MH. Managing drug-induced QT "
    "prolongation in clinical practice. Postgrad Med J. 2021;97(1149):452-8. "
    "doi:10.1136/postgradmedj-2020-138661"
)
# More than six authors, no issue, a JATS-tagged title with Markdown characters.
LONG = {
    "DOI": "10.1000/Test_2024",
    "title": ["<i>CYP2D6</i> *1/*4 carriers &amp; QT interval."],
    "author": [
        {"given": "Jean-Pierre", "family": "Dupont"},
        {"given": "Marie", "family": "Durand"},
        {"given": "Paul", "family": "Martin"},
        {"given": "Anne", "family": "Leroy"},
        {"given": "Luc", "family": "Moreau"},
        {"given": "Claire", "family": "Simon"},
        {"given": "Hugo", "family": "Laurent"},
        {"name": "Groupe Vigiking"},
    ],
    "container-title": ["Journal of Testing"],
    "short-container-title": ["J. Test."],
    "volume": "12",
    "page": "1201-1210",
    "issued": {"date-parts": [[2024, 3, 1]]},
}
LONG_VANCOUVER = (
    "Dupont JP, Durand M, Martin P, Leroy A, Moreau L, Simon C, et al. CYP2D6 \\*1/\\*4 "
    "carriers & QT interval. J Test. 2024;12:1201-10. doi:10.1000/Test\\_2024"
)
RODEN = {
    "uid": "14999113",
    "pubdate": "2004 Mar 4",
    "source": "N Engl J Med",
    "authors": [{"name": "Roden DM", "authtype": "Author"}],
    "title": "Drug-induced prolongation of the QT interval.",
    "volume": "350",
    "issue": "10",
    "pages": "1013-22",
    "articleids": [
        {"idtype": "pubmed", "value": "14999113"},
        {"idtype": "doi", "value": "10.1056/NEJMra032426"},
    ],
}
RODEN_VANCOUVER = (
    "Roden DM. Drug-induced prolongation of the QT interval. N Engl J Med. "
    "2004;350(10):1013-22. doi:10.1056/NEJMra032426"
)
SEPT = {
    "uid": "33122410",
    "pubdate": "2020 Nov",
    "source": "Drug Saf",
    "authors": [{"name": f"Auteur{c} A", "authtype": "Author"} for c in "ABCDEFG"],
    "title": "Seven authors and no issue",
    "volume": "43",
    "issue": "",
    "pages": "1131-1139",
    "articleids": [{"idtype": "pubmed", "value": "33122410"}],
}
DOIS = {"10.1136/postgradmedj-2020-138661": KHATIB, "10.1000/test_2024": LONG}
PMIDS = {"14999113": RODEN, "33122410": SEPT}


class Faux:
    """A fake `chercher`: answers from the fixtures, records each URL asked."""

    def __init__(self, erreur: Exception | None = None):
        self.erreur, self.appels = erreur, []

    def __call__(self, url: str) -> dict:
        self.appels.append(url)
        if self.erreur:
            raise self.erreur
        if url.startswith(ref.PUBMED):
            ids = url[len(ref.PUBMED) :].split(",")
            return {"result": {"uids": ids, **{i: PMIDS[i] for i in ids if i in PMIDS}}}
        doi = urllib.parse.unquote(url[len(ref.CROSSREF) :]).lower()
        if doi in DOIS:
            return {"status": "ok", "message": DOIS[doi]}
        raise LookupError(url)


def _resoudre(texte, tmp_path, chercher=None):
    return ref.resoudre(
        texte, tmp_path / "cache" / "references.json", chercher or Faux()
    )


def _liste(texte: str) -> list[str]:
    bloc = texte.split("::: {.references}\n")[1].split("\n:::")[0]
    return bloc.split("\n")


def test_citations_are_numbered_by_first_appearance_and_reused(tmp_path):
    texte, alertes = _resoudre(
        "QT long [PMID 14999113]. Prise en charge [DOI 10.1136/postgradmedj-2020-138661]."
        "\n\nRappel [pmid: 14999113].\n",
        tmp_path,
    )
    assert "QT long^1^. Prise en charge^2^." in texte
    assert "Rappel^1^." in texte
    assert _liste(texte) == [f"1. {RODEN_VANCOUVER}", f"2. {KHATIB_VANCOUVER}"]
    assert texte.rstrip().endswith(":::")
    assert "## Références {.references-page}\n\n::: {.references}\n1. " in texte
    assert alertes == []


def test_several_sources_merge_and_three_in_a_row_make_a_range(tmp_path):
    texte, _ = _resoudre(
        "A [PMID 14999113; DOI 10.1136/postgradmedj-2020-138661]. "
        "B [PMID 33122410][DOI 10.1000/test_2024]. "
        "C [PMID 14999113, PMID 33122410, DOI 10.1000/test_2024].",
        tmp_path,
    )
    assert "A^1,2^. B^3,4^. C^1,3,4^." in texte
    assert ref.exposant([10, 7, 8, 9]) == "^7–10^"
    assert ref.exposant([1, 2, 4, 5, 6]) == "^1,2,4–6^"


def test_escaped_and_unescaped_brackets_and_doi_addresses(tmp_path):
    texte, alertes = _resoudre(
        "Un \\[PMID 14999113\\], deux [doi:10.1136/postgradmedj-2020-138661], "
        "trois \\[https://doi.org/10.1000/test_2024\\], "
        "quatre \\[<https://doi.org/10.1136/postgradmedj-2020-138661>\\].",
        tmp_path,
    )
    assert "Un^1^, deux^2^, trois^3^, quatre^2^." in texte
    assert alertes == []


def test_an_escaped_underscore_inside_a_doi_is_read(tmp_path):
    faux = Faux()
    texte, alertes = _resoudre("Voir \\[DOI 10.1000/test\\_2024\\].", tmp_path, faux)
    assert "Voir^1^." in texte and _liste(texte) == [f"1. {LONG_VANCOUVER}"]
    assert faux.appels == [ref.CROSSREF + "10.1000/test_2024"]
    assert alertes == []


def test_free_text_references_are_kept_verbatim(tmp_path):
    faux = Faux()
    texte, alertes = _resoudre(
        "Données [Réf : Base nationale de pharmacovigilance, 2024]. "
        "Note \\[Ref: *Dossier interne* du CRPV\\]. Encore "
        "[Réf. base nationale de  pharmacovigilance, 2024].",
        tmp_path,
        faux,
    )
    assert "Données^1^. Note^2^. Encore^1^." in texte
    assert _liste(texte) == [
        "1. Base nationale de pharmacovigilance, 2024",
        "2. *Dossier interne* du CRPV",
    ]
    assert faux.appels == [] and alertes == []


def test_vancouver_from_crossref():
    assert ref.vancouver(ref.depuis_crossref(KHATIB)) == KHATIB_VANCOUVER
    assert ref.vancouver(ref.depuis_crossref(LONG)) == LONG_VANCOUVER
    assert (
        ref.vancouver({"titre": "Seul titre", "annee": "2020"}) == "Seul titre. 2020."
    )
    assert ref.vancouver({"titre": "Pourquoi ?", "revue": "Rev", "volume": "3"}) == (
        "Pourquoi ? Rev. 3."
    )


def test_vancouver_from_pubmed():
    assert ref.vancouver(ref.depuis_pubmed(RODEN)) == RODEN_VANCOUVER
    assert ref.vancouver(ref.depuis_pubmed(SEPT)) == (
        "AuteurA A, AuteurB A, AuteurC A, AuteurD A, AuteurE A, AuteurF A, et al. "
        "Seven authors and no issue. Drug Saf. 2020;43:1131-9."
    )


def test_initials_and_pages():
    assert ref.initiales("Jean-Pierre") == "JP"
    assert ref.initiales("Fatima R. N.") == "FRN"
    assert ref.pages_nlm("452-458") == "452-8"
    assert ref.pages_nlm("1201-1210") == "1201-10"
    assert ref.pages_nlm("99-101") == "99-101"
    assert ref.pages_nlm("1013-22") == "1013-22"
    assert ref.pages_nlm("e0123") == "e0123"


def test_pmids_go_in_one_batched_call_and_a_pmid_and_its_doi_share_a_number(tmp_path):
    faux = Faux()
    texte, alertes = _resoudre(
        "A [PMID 14999113]. B [PMID 33122410]. C [DOI 10.1056/NEJMra032426].",
        tmp_path,
        faux,
    )
    assert faux.appels[0] == ref.PUBMED + "14999113,33122410"
    assert "A^1^. B^2^. C^1^." in texte and len(_liste(texte)) == 2
    # Crossref does not know this DOI here, but PubMed gave it for PMID 14999113.
    assert alertes == []


def test_identifier_items_of_a_hand_made_list_are_formatted_in_place(tmp_path):
    source = (
        "Texte^1,2^.\n\n::: references\n1\\. Une référence écrite à la main.\n\n"
        "2\\. PMID 14999113\n\n3\\. 10.1136/postgradmedj-2020-138661\n:::\n"
    )
    texte, alertes = _resoudre(source, tmp_path)
    assert f"2\\. {RODEN_VANCOUVER}\n" in texte
    assert f"3\\. {KHATIB_VANCOUVER}\n" in texte
    assert "1\\. Une référence écrite à la main." in texte
    assert "Texte^1,2^." in texte and "references-page" not in texte
    assert alertes == []


def test_a_second_build_reads_the_cache_and_fetches_nothing(tmp_path):
    source = "A [PMID 14999113]. B [DOI 10.1000/test_2024].\n"
    premier, _ = _resoudre(source, tmp_path)
    cache = json.loads((tmp_path / "cache" / "references.json").read_text("utf-8"))
    assert cache["pmid:14999113"]["reference"] == RODEN_VANCOUVER
    assert cache["doi:10.1000/test_2024"]["reference"] == LONG_VANCOUVER
    hors_ligne = Faux(urllib.error.URLError("pas de réseau"))
    second, alertes = _resoudre(source, tmp_path, hors_ligne)
    assert second == premier and alertes == [] and hors_ligne.appels == []


def test_a_reference_not_found_is_numbered_and_reported(tmp_path):
    texte, alertes = _resoudre(
        "A [PMID 99999999]. B [DOI 10.9999/absent]. C [PMID 14999113].", tmp_path
    )
    assert "A^1^. B^2^. C^3^." in texte
    assert _liste(texte)[:2] == [
        "1. PMID 99999999 (référence non trouvée)",
        "2. DOI 10.9999/absent (référence non trouvée)",
    ]
    assert alertes == [
        "Référence introuvable : PMID 99999999 — vérifiez le numéro.",
        "Référence introuvable : DOI 10.9999/absent — vérifiez le DOI.",
    ]


def test_offline_gives_one_warning_and_writes_no_cache(tmp_path):
    faux = Faux(urllib.error.URLError("pas de réseau"))
    texte, alertes = _resoudre(
        "A [PMID 14999113]. B [DOI 10.1000/test_2024].", tmp_path, faux
    )
    assert "A^1^. B^2^." in texte
    assert "1. PMID 14999113 (référence non trouvée)" in texte
    assert alertes == [
        (
            "Pas de connexion internet : PMID 14999113, DOI 10.1000/test_2024 "
            "n'ont pas pu être vérifiées."
        )
    ]
    assert len(faux.appels) == 1
    assert not (tmp_path / "cache" / "references.json").exists()


def test_text_without_citations_is_unchanged(tmp_path):
    source = (
        '---\ntitle: "Numéro"\n---\n\n## Article {auteur="A. Nom"}\n\n'
        "Un [médicament]{.ci}, un [lien](https://doi.org/10.1/x), \\[saut\\] et 10^9^/L.\n"
    )
    faux = Faux()
    assert _resoudre(source, tmp_path, faux) == (source, [])
    assert faux.appels == []


def test_hand_typed_numbers_beside_bracket_citations_are_reported(tmp_path):
    _, alertes = _resoudre("Déjà numéroté¹ et [PMID 14999113].", tmp_path)
    assert len(alertes) == 1 and "à la main" in alertes[0]
    _, alertes = _resoudre("Déjà^3^ et [PMID 14999113].", tmp_path)
    assert len(alertes) == 1
    _, alertes = _resoudre("Plaquettes 150 10^9^/L [PMID 14999113].", tmp_path)
    assert alertes == []


def test_the_list_goes_before_the_back_cover_and_the_front_matter_is_kept(tmp_path):
    source = (
        '---\ntitle: "[PMID 1]"\n---\n\n## Article\n\nTexte [PMID 14999113].\n\n'
        "{{< include ../../commun/dos.md >}}\n"
    )
    texte, _ = _resoudre(source, tmp_path)
    assert texte.startswith('---\ntitle: "[PMID 1]"\n---\n')
    assert texte.index("## Références") < texte.index("{{< include")
    assert texte.endswith(":::\n\n{{< include ../../commun/dos.md >}}\n")


def test_a_bracket_that_is_not_understood_is_left_and_reported(tmp_path):
    texte, alertes = _resoudre("Voir [PMID 14999113; voir plus haut].", tmp_path)
    assert "[PMID 14999113; voir plus haut]" in texte
    assert alertes and alertes[0].startswith("Citation non comprise")


# --- Real escaped output from Word, through importer.py -----------------------

avec_quarto = pytest.mark.skipif(shutil.which("quarto") is None, reason="needs Quarto")

NUMERO = """---
title: "Titre"
subtitle: "Octobre 2025"
---

# Un article

Auteur : A. Dupont

Le QT s'allonge [PMID 14999113] et [DOI 10.1000/test\\_2024; PMID 33122410]. Source [Réf : Base nationale, 2024].

::: {custom-style="Références"}
1\\. PMID 14999113
:::
"""


@avec_quarto
def test_an_issue_imported_from_word_is_handled(tmp_path):
    sys.path.insert(0, str(ROOT / "bulletin" / "word"))
    spec = importlib.util.spec_from_file_location(
        "importer", ROOT / "bulletin" / "word" / "importer.py"
    )
    imp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imp)
    (tmp_path / "numero.md").write_text(NUMERO, encoding="utf-8")
    subprocess.run(
        [*imp.commande_pandoc(), "numero.md", "-o", "numero.docx"],
        cwd=tmp_path,
        check=True,
    )
    qmd = imp.importer(tmp_path / "numero.docx", "2025-10", bulletin=tmp_path / "b")
    importe = qmd.read_text(encoding="utf-8")
    assert "PMID 14999113" in importe
    texte, alertes = _resoudre(importe, tmp_path)
    assert "allonge^1^ et^2,3^. Source^4^." in texte, texte
    assert f"1\\. {RODEN_VANCOUVER}" in texte or f"1. {RODEN_VANCOUVER}" in texte
    assert _liste(texte)[3] == "4. Base nationale, 2024"
    assert len(alertes) == 1 and "à la main" in alertes[0]
