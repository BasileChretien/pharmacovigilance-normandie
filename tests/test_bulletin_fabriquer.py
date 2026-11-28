"""Tests for bulletin/fabriquer.py (the one-step build) and the map generator it relies on."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bulletin"))

import fabriquer
import make_bulletin_reseau
from verifier import Alerte


@pytest.mark.parametrize(
    ("texte", "mois"),
    [
        ("Octobre 2025", "2025-10"),
        ("décembre 2099", "2099-12"),
        ("Vigiking Normand, février 2026", "2026-02"),
        ("AOÛT 2027", "2027-08"),
        ("vigiking-2025-10", "2025-10"),
        ("Mois Année", None),
        ("", None),
    ],
)
def test_the_month_is_read_from_the_subtitle(texte, mois):
    assert fabriquer.lire_mois(texte) == mois


def test_the_month_falls_back_on_the_file_name_then_stops_with_a_plain_message(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(fabriquer, "sous_titre", lambda docx: "")
    assert (
        fabriquer.mois_du_numero(tmp_path / "Vigiking mars 2026.docx", None)
        == "2026-03"
    )
    assert fabriquer.mois_du_numero(tmp_path / "numero.docx", "2026-04") == "2026-04"
    with pytest.raises(fabriquer.Echec, match="Sous-titre"):
        fabriquer.mois_du_numero(tmp_path / "numero.docx", None)


def test_a_finding_reported_by_two_checks_is_listed_once():
    a, b = Alerte("verifier", "Couverture : texte"), Alerte("info", "autre")
    assert fabriquer.sans_doublons(
        [a, b, Alerte("verifier", "Couverture : texte")]
    ) == [a, b]


@pytest.mark.parametrize("flux", ["stdout", "stderr"])
def test_the_article_measures_are_read_from_either_stream(monkeypatch, tmp_path, flux):
    qmd = tmp_path / "vigiking-2099-01.qmd"
    qmd.with_suffix(".typ").write_text("", encoding="utf-8")
    mesures = [{"titre": "À retenir", "page": 3, "taille": 14.0, "deborde": False}]
    sortie = {"stdout": b"", "stderr": b""}
    sortie[flux] = json.dumps(mesures, ensure_ascii=False).encode("utf-8") + b"\n"
    monkeypatch.setattr(
        fabriquer.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, sortie["stdout"], sortie["stderr"]),
    )  # fmt: skip
    assert fabriquer.mesures(qmd) == mesures


def test_unreadable_measures_give_an_empty_list(monkeypatch, tmp_path):
    qmd = tmp_path / "vigiking-2099-01.qmd"
    assert fabriquer.mesures(qmd) == []  # no .typ
    qmd.with_suffix(".typ").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        fabriquer.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 1, b"", b"error: oops"),
    )
    assert fabriquer.mesures(qmd) == []


def test_the_pdf_web_page_and_list_land_next_to_the_word_file(monkeypatch, tmp_path):
    bulletin = tmp_path / "bulletin"
    qmd = bulletin / "numeros" / "2099-01" / "vigiking-2099-01.qmd"
    produits = bulletin / "_output" / "numeros" / "2099-01"
    produits.mkdir(parents=True)
    for ext in (".pdf", ".html"):
        (produits / f"vigiking-2099-01{ext}").write_text(ext, encoding="utf-8")
    monkeypatch.setattr(fabriquer, "BULLETIN", bulletin)
    word = tmp_path / "mes documents"
    word.mkdir()
    copies = fabriquer.copier_a_cote(qmd, word, "✔ Rien à signaler")
    assert [c.name for c in copies] == [
        "vigiking-2099-01.pdf", "vigiking-2099-01.html", "vigiking-2099-01 - à vérifier.txt",
    ]  # fmt: skip
    assert (
        (word / "vigiking-2099-01 - à vérifier.txt")
        .read_text(encoding="utf-8")
        .startswith("✔")
    )


def test_a_file_that_is_neither_word_nor_an_issue_stops(tmp_path):
    with pytest.raises(fabriquer.Echec, match="docx"):
        fabriquer.fabriquer(tmp_path / "numero.pdf", None, avec_liens=False)


def test_the_map_becomes_a_typst_string_and_refuses_a_dollar():
    texte = make_bulletin_reseau.typst('<svg a="1">\\</svg>')
    assert '#let reseau-svg = bytes("<svg a=\\"1\\">\\\\</svg>")' in texte
    with pytest.raises(ValueError):
        make_bulletin_reseau.typst("<svg>$</svg>")


def test_the_committed_map_is_up_to_date():
    data = json.loads(make_bulletin_reseau.DATA.read_text(encoding="utf-8"))
    attendu = make_bulletin_reseau.typst(make_bulletin_reseau.svg(data))
    assert (make_bulletin_reseau.OUT / "reseau.typ").read_text(
        encoding="utf-8"
    ) == attendu
