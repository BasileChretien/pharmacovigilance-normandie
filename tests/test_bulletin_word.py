"""Tests for bulletin/word/importer.py: an issue written in Word becomes the bulletin's text."""

import base64
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "importer", ROOT / "bulletin" / "word" / "importer.py"
)
imp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(imp)

avec_pandoc = pytest.mark.skipif(
    shutil.which("quarto") is None and shutil.which("pandoc") is None,
    reason="needs pandoc (Quarto's)",
)

# What an author writes in Word, as Markdown that pandoc turns into the .docx.
NUMERO = """---
title: "Titre du dossier"
subtitle: "Octobre 2025"
---

![Illustration de couverture](point.png)

# Un article en deux colonnes

Auteur : A. Dupont

Texte avec **gras**, un [médicament]{custom-style="Contre-indication"} et un [autre]{custom-style="CredibleMeds"}.

::: {custom-style="Encadré"}
Message clé.

Suite du message.
:::

[saut de colonne]

![Légende de test](point.png){width=3.25in}

# Un article en une colonne

Auteurs : B. Martin, C. Durand

Texte seul.

# Une liste

::: {custom-style="Catégorie rouge"}
Cardiologie
:::

Classe : [x]{custom-style="Contre-indication"}
"""
# A 1x1 PNG, for the figure.
POINT = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


def _docx(tmp_path: Path) -> Path:
    (tmp_path / "numero.md").write_text(NUMERO, encoding="utf-8")
    (tmp_path / "point.png").write_bytes(POINT)
    subprocess.run(
        [*imp.commande_pandoc(), "numero.md", "-o", "numero.docx"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path / "numero.docx"


def _titres(texte: str) -> list[str]:
    return [ligne for ligne in texte.splitlines() if ligne.startswith("## ")]


@avec_pandoc
def test_a_word_issue_becomes_the_bulletin_text(tmp_path):
    sortie = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path / "bulletin")
    texte = sortie.read_text(encoding="utf-8")
    assert (
        sortie == tmp_path / "bulletin" / "numeros" / "2025-10" / "vigiking-2025-10.qmd"
    )
    assert "numero: Octobre 2025" in texte
    assert "pdf: vigiking-2025-10.pdf" in texte
    assert "output-file: vigiking-2025-10.pdf" in texte
    assert "output-file: vigiking-2025-10.html" in texte
    assert "[médicament]{.ci}" in texte and "[autre]{.cm}" in texte
    assert "::: encadre" in texte
    assert "custom-style" not in texte and "Auteur :" not in texte


@avec_pandoc
def test_columns_follow_the_column_break_and_category_labels_make_a_list(tmp_path):
    texte = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path).read_text(
        encoding="utf-8"
    )
    deux, une, liste = _titres(texte)
    premier, second, _ = texte.split("\n## ")[1:]
    assert 'auteur="A. Dupont"' in deux and "saut-colonne" in premier
    assert 'auteur="B. Martin, C. Durand"' in une and "saut-colonne" not in second
    assert ".liste" in liste
    assert 'couleur="rouge"' in texte


@avec_pandoc
def test_a_picture_and_its_caption_become_a_figure(tmp_path):
    sortie = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path)
    texte = sortie.read_text(encoding="utf-8")
    image = re.search(r"!\[Légende de test\]\((images/[^)]+)\)", texte)
    assert image, texte
    assert (sortie.parent / image.group(1)).is_file()
    # Half of Word's text width (6.5 in): half the column.
    assert re.search(r"!\[Légende de test\]\(images/[^)]+\)\{[^}]*width=\"50%\"", texte)


@avec_pandoc
def test_the_word_alternative_text_of_a_picture_is_kept(tmp_path):
    # pandoc writes the Markdown alt text as the Word picture's alternative text (descr).
    texte = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path).read_text(
        encoding="utf-8"
    )
    assert re.search(r"!\[Légende de test\]\(images/[^)]+\)\{[^}]*fig-alt=\"Légende de test\"", texte), texte


@avec_pandoc
def test_shared_logos_and_back_cover_are_used_when_present(tmp_path):
    commun = tmp_path / "commun"
    commun.mkdir()
    (commun / "logo-rouen.png").write_bytes(POINT)
    (commun / "dos.md").write_text("## Dos {.dos}\n", encoding="utf-8")
    sortie = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path)
    texte = sortie.read_text(encoding="utf-8")
    assert "logo-gauche: images/logo-rouen.png" in texte
    assert (sortie.parent / "images" / "logo-rouen.png").is_file()
    assert "logo-droite" not in texte
    assert "{{< include ../../commun/dos.md >}}" in texte


@avec_pandoc
def test_an_existing_issue_is_not_overwritten_unless_asked(tmp_path):
    docx = _docx(tmp_path)
    imp.importer(docx, "2025-10", bulletin=tmp_path)
    with pytest.raises(SystemExit):
        imp.importer(docx, "2025-10", bulletin=tmp_path)
    assert imp.importer(docx, "2025-10", bulletin=tmp_path, remplacer=True).is_file()


def test_a_bad_month_or_a_missing_file_stops(tmp_path):
    with pytest.raises(SystemExit):
        imp.importer(tmp_path / "numero.docx", "2025-13", bulletin=tmp_path)
    with pytest.raises(SystemExit):
        imp.importer(tmp_path / "absent.docx", "2025-10", bulletin=tmp_path)


_spec_modele = importlib.util.spec_from_file_location(
    "faire_modele", ROOT / "bulletin" / "word" / "faire_modele.py"
)


def _faire_modele():
    import sys

    sys.path.insert(0, str(ROOT / "bulletin" / "word"))
    module = importlib.util.module_from_spec(_spec_modele)
    _spec_modele.loader.exec_module(module)
    return module


def _style(nom: str, kind: str = "paragraph") -> str:
    return (
        f'<w:style w:type="{kind}" w:customStyle="1" w:styleId="x">'
        f'<w:name w:val="{nom}" /><w:basedOn w:val="BodyText" /></w:style>'
    )


def test_the_word_template_styles_get_the_bulletin_look():
    fm = _faire_modele()
    styles = "<w:styles>" + "".join(_style(nom) for nom in fm.LOOKS) + "</w:styles>"
    resultat = fm.styler(styles)
    contre_indication = re.search(
        r'<w:name w:val="Contre-indication" />.*?</w:style>', resultat
    ).group(0)
    assert (
        '<w:color w:val="C00000"/>' in contre_indication
        and "<w:b/>" in contre_indication
    )
    encadre = re.search(r'<w:name w:val="Encadré" />.*?</w:style>', resultat).group(0)
    assert 'w:fill="EEF3FA"' in encadre and "<w:pBdr>" in encadre


def test_a_style_missing_from_the_template_source_stops():
    fm = _faire_modele()
    with pytest.raises(SystemExit):
        fm.styler("<w:styles>" + _style("Encadré") + "</w:styles>")


@avec_pandoc
def test_a_picture_before_the_first_article_is_the_cover(tmp_path):
    texte = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path).read_text(
        encoding="utf-8"
    )
    assert re.search(r"couverture: images/\S+", texte)
    assert "couverture-alt: Illustration de couverture" in texte
    assert "![Illustration de couverture]" not in texte


@avec_pandoc
def test_consecutive_paragraphs_of_one_style_make_one_box(tmp_path):
    texte = imp.importer(_docx(tmp_path), "2025-10", bulletin=tmp_path).read_text(
        encoding="utf-8"
    )
    assert texte.count("::: encadre") == 1
    assert "::: encadre\nMessage clé.\n\nSuite du message.\n:::" in texte
