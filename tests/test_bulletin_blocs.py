"""Types of content: "Bloc …" styles (the template's and authors' own), rubrics, editorial,
key figures, source lines, run-in headings and subheadings, from Word to the layout."""

import base64
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from check_contrast import contrast_ratio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bulletin" / "word"))

import importer as imp

FILTRE_RENDU = ROOT / "bulletin" / "_extensions" / "vigiking" / "vigiking.lua"
W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
avec_pandoc = pytest.mark.skipif(
    shutil.which("quarto") is None and shutil.which("pandoc") is None,
    reason="needs pandoc (Quarto's)",
)


def _style(
    sid: str, nom: str, couleur: str | None = None, base: str | None = None
) -> str:
    base_xml = f'<w:basedOn w:val="{base}"/>' if base else ""
    rpr = f'<w:rPr><w:color w:val="{couleur}"/></w:rPr>' if couleur else ""
    return (
        f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{nom}"/>'
        f"{base_xml}{rpr}</w:style>"
    )


def _docx_styles(tmp_path: Path, *styles: str) -> Path:
    chemin = tmp_path / "styles.docx"
    with zipfile.ZipFile(chemin, "w") as paquet:
        paquet.writestr(
            "word/styles.xml", f"<w:styles {W_NS}>{''.join(styles)}</w:styles>"
        )
    return chemin


def test_a_block_style_gives_its_font_colour_or_the_one_it_is_based_on(tmp_path):
    docx = _docx_styles(
        tmp_path,
        _style("Rouge", "Mon rouge", "C00000"),
        _style("A", "Bloc Interaction", "1F7A4D"),
        _style("B", "Bloc : Erreur", base="Rouge"),
        _style("C", "Bloc Sans couleur", "000000"),
        _style("D", "Bloc Automatique", "auto"),
        _style("E", "Blocage", "123456"),
        _style("F", "Encadré", "2F5597"),
    )
    assert imp.couleurs_des_blocs(docx) == {
        "Bloc Interaction": "#1f7a4d",
        "Bloc : Erreur": "#c00000",
    }


def test_the_template_gives_every_built_in_type_its_colour():
    couleurs = imp.couleurs_des_blocs(
        ROOT / "bulletin" / "word" / "modele-vigiking.docx"
    )
    for nom in (
        "Bloc Cas clinique",
        "Bloc À retenir",
        "Bloc En pratique",
        "Bloc Attention",
    ):
        assert re.fullmatch(r"#[0-9a-f]{6}", couleurs[nom]), nom
    assert len(couleurs) == 10


# What an author writes in Word, as Markdown that pandoc turns into the .docx.
NUMERO = """---
title: "Titre"
subtitle: "Mars 2099"
---

::: {custom-style="Éditorial"}
Un mot d'accueil.
:::

# Un article

Auteur : A. Dupont

Rubrique : Littérature

Relecture : B. Martin

[Mécanisme]{custom-style="Intertitre en ligne"} le blocage du canal.

::: {custom-style="Bloc Interaction"}
Premier paragraphe.
:::

::: {custom-style="Bloc Interaction"}
Second paragraphe, même bloc.
:::

::: {custom-style="Chiffre clé"}
66 % des cas.
:::

::: {custom-style="Chiffre clé"}
20 jours de délai.
:::

## Une brève

Le texte de la brève.

::: {custom-style="Source"}
Source : ANSM, 1er mars 2099.
:::
"""
POINT = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


def _colorer(docx: Path, nom: str, couleur: str) -> None:
    """Give a style of the .docx a font colour, as an author does in Word."""
    with zipfile.ZipFile(docx) as entree:
        parties = {i.filename: entree.read(i.filename) for i in entree.infolist()}
    styles = parties["word/styles.xml"].decode("utf-8")
    motif = re.compile(
        r'(<w:style [^>]*>\s*<w:name w:val="' + re.escape(nom) + r'"\s*/>)'
    )
    styles, n = motif.subn(rf'\1<w:rPr><w:color w:val="{couleur}"/></w:rPr>', styles)
    assert n == 1, nom
    parties["word/styles.xml"] = styles.encode("utf-8")
    with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as sortie:
        for nom_partie, data in parties.items():
            sortie.writestr(nom_partie, data)


@pytest.fixture
def numero_importe(tmp_path):
    (tmp_path / "numero.md").write_text(NUMERO, encoding="utf-8")
    subprocess.run(
        [*imp.commande_pandoc(), "numero.md", "-o", "numero.docx"],
        cwd=tmp_path,
        check=True,
    )
    _colorer(tmp_path / "numero.docx", "Bloc Interaction", "1F7A4D")
    sortie = imp.importer(tmp_path / "numero.docx", "2099-03", bulletin=tmp_path / "b")
    return sortie.read_text(encoding="utf-8")


@avec_pandoc
def test_an_author_block_style_becomes_one_titled_block_in_its_colour(numero_importe):
    blocs = re.findall(r"^::: \{\.bloc([^}]*)\}", numero_importe, re.MULTILINE)
    assert len(blocs) == 1, numero_importe  # two paragraphs, one block
    assert 'titre="Interaction"' in blocs[0] and 'couleur="#1f7a4d"' in blocs[0]
    assert "Second paragraphe, même bloc." in numero_importe


@avec_pandoc
def test_rubric_reviewer_editorial_figures_source_and_subheadings_come_through(
    numero_importe,
):
    titre = next(l for l in numero_importe.splitlines() if l.startswith("## "))
    assert 'auteur="A. Dupont"' in titre and 'rubrique="Littérature"' in titre
    assert 'relecture="B. Martin"' in titre
    assert "Rubrique :" not in numero_importe and "Relecture :" not in numero_importe
    assert "::: editorial" in numero_importe
    assert numero_importe.count("::: chiffres") == 1  # two paragraphs, one row of tiles
    assert "::: source" in numero_importe
    assert "[Mécanisme]{.intertitre}" in numero_importe
    assert "### Une brève" in numero_importe  # "Titre 2": a subheading, not an article


def _rendre(markdown: str, format_sortie: str) -> str:
    return subprocess.run(
        [*imp.commande_pandoc(), "-f", "markdown", "-t", format_sortie, f"--lua-filter={FILTRE_RENDU}"],
        input=markdown, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout  # fmt: skip


@avec_pandoc
@pytest.mark.parametrize("couleur", ["#ffd400", "#2a8fbd", "#0d4a5e", "#ffffff"])
def test_any_block_colour_is_made_readable_on_its_tint(couleur):
    typst = _rendre(
        f'::: {{.bloc titre="Type" couleur="{couleur}"}}\nTexte.\n:::\n', "typst"
    )
    trouve = re.search(
        r'#bloc\(titre: "Type", couleur: rgb\("(#\w{6})"\), fond: rgb\("(#\w{6})"\)\)',
        typst,
    )
    assert trouve, typst
    assert contrast_ratio(trouve[1], trouve[2]) >= 4.5


@avec_pandoc
def test_a_block_without_colour_takes_the_article_colour():
    typst = _rendre('::: {.bloc titre="Type"}\nTexte.\n:::\n', "typst")
    assert '#bloc(titre: "Type")[' in typst


@avec_pandoc
def test_key_figures_split_the_number_from_what_it_counts():
    typst = _rendre(
        "::: chiffres\n66 % des cas graves.\n\n1 200 déclarations.\n\nSans nombre.\n:::\n",
        "typst",
    )
    assert (
        '#chiffres(("66 %", "des cas graves."), ("1 200", "déclarations."), ("", "Sans nombre."))'
        in typst
    )


@avec_pandoc
def test_the_web_page_gets_the_block_colours_and_the_tiles():
    html = _rendre(
        '::: {.bloc titre="Type" couleur="#b3261e"}\nTexte.\n:::\n\n::: chiffres\n66 % des cas.\n:::\n',
        "html",
    )
    assert (
        'data-titre="Type"' in html
        and "--bloc: #b3261e" in html
        and "--bloc-fond: #" in html
    )
    assert '<span class="nombre">66 %</span>' in html
