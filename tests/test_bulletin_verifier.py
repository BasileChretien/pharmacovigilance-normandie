"""Tests for bulletin/word/verifier.py: the author's to-do list before sending an issue."""

import base64
import importlib.util
import shutil
import socket
import struct
import subprocess
import sys
import urllib.error
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "verifier", ROOT / "bulletin" / "word" / "verifier.py"
)
ver = importlib.util.module_from_spec(_spec)
sys.modules["verifier"] = ver  # dataclasses look the module up
_spec.loader.exec_module(ver)

avec_pandoc = pytest.mark.skipif(
    shutil.which("quarto") is None and shutil.which("pandoc") is None,
    reason="needs pandoc (Quarto's)",
)

# --- Word files written part by part --------------------------------------------------

NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
    'xmlns:adec="http://schemas.microsoft.com/office/drawing/2017/decorative"'
)
# Style id -> (type, name), as Word writes them.
STYLES = {
    "Title": ("paragraph", "Title"),
    "Subtitle": ("paragraph", "Subtitle"),
    "Titre1": ("paragraph", "heading 1"),
    "Titre2": ("paragraph", "heading 2"),
    "BodyText": ("paragraph", "Body Text"),
    "ListParagraph": ("paragraph", "List Paragraph"),
    "Caption": ("paragraph", "caption"),
    "Encadr": ("paragraph", "Encadré"),
    "Perso": ("paragraph", "Mon encadré vert"),
    "BlocPerso": ("paragraph", "Bloc Interaction"),
    "CI": ("character", "Contre-indication"),
}


def _styles_xml() -> str:
    styles = "".join(
        f'<w:style w:type="{t}" w:styleId="{i}"><w:name w:val="{n}"/></w:style>'
        for i, (t, n) in STYLES.items()
    )
    return f"<w:styles {NS}>{styles}</w:styles>"


def _r(texte: str, rpr: str = "") -> str:
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{texte}</w:t></w:r>'


def _p(contenu: str, style: str | None = None, ppr: str = "") -> str:
    pstyle = f'<w:pStyle w:val="{style}"/>' if style else ""
    return f"<w:p><w:pPr>{pstyle}{ppr}</w:pPr>{contenu}</w:p>"


def _texte(texte: str, style: str | None = None) -> str:
    return _p(_r(texte), style)


def _image(descr: str | None = "Une figure", decoratif: bool = False) -> str:
    alt = f' descr="{descr}"' if descr is not None else ""
    deco = (
        '<a:extLst><a:ext uri="{C183D7F6-B498-43B3-948B-1728B52AA6E4}">'
        '<adec:decorative val="1"/></a:ext></a:extLst>'
        if decoratif
        else ""
    )
    return (
        f'<w:r><w:drawing><wp:inline><wp:docPr id="1" name="Image 1"{alt}>{deco}'
        "</wp:docPr><a:graphic><a:graphicData><pic:pic/></a:graphicData></a:graphic>"
        "</wp:inline></w:drawing></w:r>"
    )


DEBUT = _texte("Titre du dossier", "Title") + _texte("Octobre 2025", "Subtitle")


def _docx(tmp_path: Path, corps: str, debut: str = DEBUT) -> Path:
    chemin = tmp_path / "numero.docx"
    with zipfile.ZipFile(chemin, "w") as paquet:
        paquet.writestr("word/styles.xml", _styles_xml())
        paquet.writestr(
            "word/document.xml",
            f"<w:document {NS}><w:body>{debut}{corps}</w:body></w:document>",
        )
    return chemin


def _messages(alertes, niveau=None) -> list[str]:
    return [a.message for a in alertes if niveau is None or a.niveau == niveau]


ROUGE = '<w:color w:val="FF0000"/>'


def test_the_word_template_itself_raises_nothing():
    assert ver.verifier_docx(ROOT / "bulletin" / "word" / "modele-vigiking.docx") == []


def test_hand_colour_is_flagged_by_article_and_consecutive_runs_make_one_passage(
    tmp_path,
):
    corps = (
        _texte("Allongement du QT", "Titre1")
        + _p(_r("Texte ") + _r("amio", ROUGE) + _r("darone", ROUGE) + _r(" seul."))
        + _texte("Hépatites", "Titre1")
        + _p(_r("surligné", '<w:highlight w:val="yellow"/>'))
        + _p(_r("ombré", '<w:shd w:val="clear" w:fill="FFC000"/>'))
    )
    alertes = ver.verifier_docx(_docx(tmp_path, corps))
    couleurs = [m for m in _messages(alertes, "corriger") if "couleur" in m]
    assert couleurs == [
        (
            "Article « Allongement du QT » : couleur mise à la main sur « amiodarone » — "
            "elle sera perdue. Utilisez le style « Contre-indication » (rouge) ou "
            "« CredibleMeds » (orange)."
        ),
        couleurs[1],
    ]
    assert couleurs[1].startswith("Article « Hépatites » : couleur mise à la main sur")
    assert "« surligné », « ombré »" in couleurs[1]


def test_template_character_styles_and_black_or_automatic_colours_pass(tmp_path):
    corps = (
        _texte("Article", "Titre1")
        + _p(_r("contre-indiqué", f'<w:rStyle w:val="CI"/>{ROUGE}'))
        + _p(
            _r("noir", '<w:color w:val="000000"/>')
            + _r("auto", '<w:color w:val="auto"/>')
        )
        + _p(f"<w:hyperlink>{_r('lien', ROUGE)}</w:hyperlink>")
    )
    assert ver.verifier_docx(_docx(tmp_path, corps)) == []


def test_many_coloured_passages_are_capped_in_one_message(tmp_path):
    passages = "".join(_p(_r(f"mot{i}", ROUGE)) for i in range(5))
    alertes = ver.verifier_docx(_docx(tmp_path, _texte("Liste", "Titre1") + passages))
    (message,) = _messages(alertes)
    assert "« mot0 », « mot1 », « mot2 » et 2 autres passages" in message


def test_a_long_coloured_passage_is_cut(tmp_path):
    corps = _texte("A", "Titre1") + _p(_r("x" * 100, ROUGE))
    (message,) = _messages(ver.verifier_docx(_docx(tmp_path, corps)))
    assert "x" * 39 + "…" in message and "x" * 41 not in message


def test_hand_shading_of_a_paragraph_is_flagged_but_not_the_template_box(tmp_path):
    fond = '<w:shd w:val="clear" w:fill="C6EFCE"/>'
    corps = (
        _texte("Encadrés", "Titre1")
        + _p(_r("Boîte faite main"), ppr=fond)
        + _p(_r("Boîte du modèle"), "Encadr", ppr=fond)
    )
    (message,) = _messages(ver.verifier_docx(_docx(tmp_path, corps)), "verifier")
    assert message.startswith(
        "Article « Encadrés » : fond coloré mis à la main sur « Boîte faite main »"
    )
    assert "« Encadré »" in message


def test_pictures_without_alternative_text_are_counted_by_article(tmp_path):
    corps = (
        _p(_image(None))
        + _texte("Figures", "Titre1")
        + _p(_image(""))
        + _p(_image("   "))
        + _p(_image("Courbe de survie"))
        + _p(_image(None, decoratif=True))
    )
    images = [
        m
        for m in _messages(ver.verifier_docx(_docx(tmp_path, corps)))
        if "remplacement" in m
    ]
    assert images == [
        (
            "Couverture : l'image n'a pas de texte de remplacement, lu par les lecteurs d'écran "
            "(dans Word : clic droit sur l'image → Modifier le texte de remplacement)."
        ),
        images[1],
    ]
    assert images[1].startswith(
        "Article « Figures » : 2 images n'ont pas de texte de remplacement"
    )


def test_a_picture_with_alternative_text_passes(tmp_path):
    corps = _texte("Figure", "Titre1") + _p(_image("Courbe"))
    assert ver.verifier_docx(_docx(tmp_path, corps)) == []


def test_a_missing_or_empty_subtitle_must_be_fixed(tmp_path):
    for debut in (
        _texte("Titre", "Title"),
        _texte("Titre", "Title") + _p("", "Subtitle"),
    ):
        alertes = ver.verifier_docx(_docx(tmp_path, _texte("A", "Titre1"), debut))
        assert [a.niveau for a in alertes] == ["corriger"]
        assert "« Octobre 2025 »" in alertes[0].message
        assert "« Sous-titre »" in alertes[0].message


def test_a_style_unknown_to_the_template_is_flagged_once_with_its_count(tmp_path):
    corps = (
        _texte("Encadré vert", "Titre1")
        + _texte("un", "Perso")
        + _texte("deux", "Perso")
        + _texte("trois", "Perso")
        + _texte("liste", "ListParagraph")
        + _texte("corps", "BodyText")
        + _texte("légende", "Caption")
        + _texte("boîte", "Encadr")
        + _texte("normal")
    )
    (message,) = _messages(ver.verifier_docx(_docx(tmp_path, corps)))
    assert message.startswith(
        "Article « Encadré vert » : le style « Mon encadré vert » (et 2 autres "
        "paragraphes) ne fait pas partie du modèle"
    )


def test_unknown_styles_are_capped(tmp_path):
    STYLES.update({f"S{i}": ("paragraph", f"Style {i}") for i in range(7)})
    try:
        corps = _texte("A", "Titre1") + "".join(_texte("x", f"S{i}") for i in range(7))
        messages = _messages(ver.verifier_docx(_docx(tmp_path, corps)))
    finally:
        for i in range(7):
            del STYLES[f"S{i}"]
    assert len(messages) == ver.STYLES_SIGNALES_MAX + 1
    assert messages[-1].startswith("… et 2 autre(s) style(s)")


def test_a_block_type_an_author_created_raises_nothing(tmp_path):
    corps = _texte("Article", "Titre1") + _texte("Une interaction.", "BlocPerso")
    assert _messages(ver.verifier_docx(_docx(tmp_path, corps)), "verifier") == []


def test_a_heading_2_is_a_subheading_and_raises_nothing(tmp_path):
    corps = _texte("Article", "Titre1") + _texte("Intertitre", "Titre2")
    assert _messages(ver.verifier_docx(_docx(tmp_path, corps)), "verifier") == []


def test_a_file_that_is_not_a_word_document_stops(tmp_path):
    faux = tmp_path / "faux.docx"
    faux.write_text("pas un zip", encoding="utf-8")
    with pytest.raises(SystemExit):
        ver.verifier_docx(faux)


POINT = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


@avec_pandoc
def test_a_word_file_made_by_pandoc_is_read_with_its_styles(tmp_path):
    (tmp_path / "point.png").write_bytes(POINT)
    (tmp_path / "numero.md").write_text(
        '---\ntitle: "T"\nsubtitle: "Octobre 2025"\n---\n\n# Un article\n\n'
        'Un [médicament]{custom-style="Contre-indication"}.\n\n'
        '::: {custom-style="Mon style"}\nTexte.\n:::\n\n![](point.png)\n',
        encoding="utf-8",
    )
    subprocess.run(
        [shutil.which("quarto") or shutil.which("pandoc"), *(["pandoc"] if shutil.which("quarto") else []),
         "numero.md", "-o", "numero.docx"],
        cwd=tmp_path,
        check=True,
    )  # fmt: skip
    messages = _messages(ver.verifier_docx(tmp_path / "numero.docx"))
    assert len(messages) == 2, messages
    assert messages[0].startswith("Article « Un article » : une image n'a pas de texte")
    assert messages[1].startswith("Article « Un article » : le style « Mon style »")


# --- The imported issue -----------------------------------------------------------------


def _png(largeur: int, hauteur: int = 10) -> bytes:
    ihdr = struct.pack(">II", largeur, hauteur) + b"\x08\x02\x00\x00\x00"
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\0" * 4


def _jpeg(largeur: int, hauteur: int = 10) -> bytes:
    app0 = (
        b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x01\x01\x00" + b"\0" * 6
    )
    sof = b"\xff\xc0" + struct.pack(">HBHH", 17, 8, hauteur, largeur) + b"\0" * 9
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


def _gif(largeur: int, hauteur: int = 10) -> bytes:
    return b"GIF89a" + struct.pack("<HH", largeur, hauteur) + b"\0" * 8


def test_picture_widths_are_read_from_their_headers(tmp_path):
    for nom, data, largeur in (
        ("a.png", _png(1200), 1200),
        ("b.jpg", _jpeg(640), 640),
        ("c.gif", _gif(320), 320),
        ("d.svg", b"<svg/>", None),
    ):
        (tmp_path / nom).write_bytes(data)
        assert ver._largeur(tmp_path / nom) == largeur


NUMERO = """---
title: "Titre du dossier"
couverture: images/couverture.png
couverture-alt: "Gélules sur une table"
numero: Octobre 2025
---

## Un article complet {auteur="A. Dupont"}

Texte, figure nette :

![Courbe de survie](images/grande.png){width="50%" fig-alt="Courbe qui descend"}

Une icône ![Alerte rouge](images/grande.png) dans le texte.

## Une liste {.liste auteur="[auteur]"}

Texte \\[à compléter : source\\] et encore [à compléter].

## Sans auteur

![Petite photo](images/petite.jpg){width="30%"}

![](images/absente.png)

![Schéma](images/schema.emf){fig-alt="Un schéma"}

## Pour nous joindre {.dos}

Coordonnées.
"""


def _numero(tmp_path: Path, texte: str = NUMERO) -> Path:
    images = tmp_path / "images"
    images.mkdir(exist_ok=True)
    (images / "couverture.png").write_bytes(_png(1600))
    (images / "grande.png").write_bytes(_png(1200))
    (images / "petite.jpg").write_bytes(_jpeg(640))
    (images / "schema.emf").write_bytes(b"\x01\x00\x00\x00")
    qmd = tmp_path / "vigiking-2025-10.qmd"
    qmd.write_text(texte, encoding="utf-8")
    return qmd


def test_the_issue_check_lists_each_problem_where_it_is(tmp_path):
    alertes = ver.verifier_numero(_numero(tmp_path))
    assert [(a.niveau, a.message.split(" : ")[0]) for a in alertes] == [
        ("verifier", "Article « Une liste »"),  # author placeholder
        ("corriger", "Article « Une liste »"),  # [à compléter]
        ("verifier", "Article « Sans auteur »"),  # no author
        ("verifier", "Article « Sans auteur »"),  # small photo, no fig-alt
        ("verifier", "Article « Sans auteur »"),  # small photo, 640 px
        ("verifier", "Article « Sans auteur »"),  # absent picture, no alt
        ("corriger", "Article « Sans auteur »"),  # absent picture
        ("corriger", "Article « Sans auteur »"),  # EMF
    ]
    messages = _messages(alertes)
    assert "le nom de l'auteur est à compléter" in messages[0]
    assert "« [à compléter : source] », « [à compléter] »" in messages[1]
    assert messages[3].startswith(
        "Article « Sans auteur » : l'image « Petite photo » n'a pas de texte"
    )
    assert "(640 pixels de large)" in messages[4]
    assert (
        "l'image n° 2 (sans légende) est introuvable (images/absente.png)"
        in messages[6]
    )
    assert "au format EMF" in messages[7]


def test_a_complete_issue_with_its_cover_raises_nothing(tmp_path):
    debut, _ = NUMERO.split("## Une liste")
    assert ver.verifier_numero(_numero(tmp_path, debut)) == []


def test_without_a_cover_a_graphic_one_is_made(tmp_path):
    texte = '---\ntitle: T\n---\n\n## A {auteur="A. B"}\n\nTexte.\n'
    alertes = ver.verifier_numero(_numero(tmp_path, texte))
    assert [a.niveau for a in alertes] == ["info"]
    assert "couverture graphique" in alertes[0].message


def test_the_cover_picture_is_checked_like_the_others(tmp_path):
    texte = (
        '---\ntitle: T\ncouverture: "images/rien.png"\n---\n\n## A {auteur="A. B"}\n'
    )
    alertes = ver.verifier_numero(_numero(tmp_path, texte))
    assert [(a.niveau, a.message.split(" : ")[0]) for a in alertes] == [
        ("verifier", "Couverture"),
        ("corriger", "Couverture"),
    ]
    texte = "---\ntitle: T\ncouverture: images/petite.jpg\ncouverture-alt: Photo\n---\n"
    (alerte,) = ver.verifier_numero(_numero(tmp_path, texte))
    assert alerte.message.startswith("Couverture : l'image est petite (640 pixels")


def test_a_placeholder_in_the_title_is_flagged(tmp_path):
    texte = '---\ntitle: "[à compléter]"\ncouverture: images/grande.png\ncouverture-alt: x\n---\n'
    (alerte,) = ver.verifier_numero(_numero(tmp_path, texte))
    assert alerte.niveau == "corriger" and alerte.message.startswith(
        "Titre ou sous-titre"
    )


def test_a_missing_issue_stops(tmp_path):
    with pytest.raises(SystemExit):
        ver.verifier_numero(tmp_path / "absent.qmd")


# --- Page measures ---------------------------------------------------------------------


def test_overflowing_and_small_print_articles_are_flagged_with_their_page():
    alertes = ver.verifier_mesures(
        [
            {"titre": "Long", "page": 3, "taille": 9, "deborde": True},
            {"titre": "Serré", "page": 4, "taille": 11.5, "deborde": False},
            {"titre": "Limite", "page": 5, "taille": 12, "deborde": False},
            {"titre": "Aéré", "page": 6, "taille": 16, "deborde": False},
        ]
    )
    assert [(a.niveau, a.message.split(" : ")[0]) for a in alertes] == [
        ("corriger", "Article « Long » (page 3)"),
        ("verifier", "Article « Serré » (page 4)"),
        ("verifier", "Article « Limite » (page 5)"),
    ]
    assert "coupez-le en deux articles (un nouveau « Titre 1 »)" in alertes[0].message
    assert "(11,5 pt)" in alertes[1].message and "(12 pt)" in alertes[2].message


# --- Links ----------------------------------------------------------------------------


def test_links_are_found_cleaned_and_deduplicated():
    texte = (
        "Voir [l'ANSM](https://ansm.sante.fr/actualites/x) et <https://www.ema.europa.eu/fr>.\n"
        "Adresse nue : https://example.org/page. Encore (https://example.org/autre), "
        "https://fr.wikipedia.org/wiki/Torsade_(cardiologie) ; **https://gras.fr/a**\n"
        "Doublon https://ansm.sante.fr/actualites/x, courriel <mailto:crpv@chu.fr>, "
        "échappé https://x.org/a\\_b\n"
    )
    assert ver.liens(texte) == [
        "https://ansm.sante.fr/actualites/x",
        "https://www.ema.europa.eu/fr",
        "https://example.org/page",
        "https://example.org/autre",
        "https://fr.wikipedia.org/wiki/Torsade_(cardiologie)",
        "https://gras.fr/a",
        "https://x.org/a_b",
    ]


def _faux(reponses: dict):
    def chercher(url: str) -> int:
        reponse = reponses[url]
        if isinstance(reponse, Exception):
            raise reponse
        return reponse

    return chercher


def test_dead_links_must_be_fixed_and_refused_checks_verified():
    reponses = {
        "https://ok.fr": 200,
        "https://redirige.fr": 301,
        "https://mort.fr/a": 404,
        "https://parti.fr": 410,
        "https://inconnu.invalid": urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed")),
        "https://refus.fr": 403,
        "https://panne.fr": 503,
        "https://lent.fr": urllib.error.URLError(TimeoutError("timed out")),
        "https://lent2.fr": TimeoutError("timed out"),
    }  # fmt: skip
    alertes = ver.verifier_liens(list(reponses), chercher=_faux(reponses))
    assert [(a.niveau, a.message.split(" (")[0]) for a in alertes] == [
        ("corriger", "Lien mort : https://mort.fr/a"),
        ("corriger", "Lien mort : https://parti.fr"),
        ("corriger", "Lien mort : https://inconnu.invalid"),
        ("verifier", "Lien à vérifier : https://refus.fr"),
        ("verifier", "Lien à vérifier : https://panne.fr"),
        ("verifier", "Lien à vérifier : https://lent.fr"),
        ("verifier", "Lien à vérifier : https://lent2.fr"),
    ]
    assert (
        "erreur 404" in alertes[0].message and "site introuvable" in alertes[2].message
    )
    assert "code 403" in alertes[3].message and "à temps" in alertes[5].message


def test_without_any_network_one_note_says_links_were_not_checked():
    hors_ligne = urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))
    urls = ["https://a.fr", "https://b.fr"]
    alertes = ver.verifier_liens(urls, chercher=_faux(dict.fromkeys(urls, hors_ligne)))
    assert [(a.niveau, a.message) for a in alertes] == [
        ("info", "Les liens n'ont pas été vérifiés : pas de connexion Internet.")
    ]
    assert ver.verifier_liens([], chercher=_faux({})) == []


class _Reponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_the_default_check_tries_get_when_head_is_refused(monkeypatch):
    requetes = []

    def urlopen(requete, timeout):
        requetes.append(
            (requete.get_method(), requete.get_header("User-agent"), timeout)
        )
        if requete.get_method() == "HEAD":
            raise urllib.error.HTTPError(
                requete.full_url, 405, "Method Not Allowed", {}, None
            )
        return _Reponse()

    monkeypatch.setattr(ver.urllib.request, "urlopen", urlopen)
    assert ver._chercher("https://exemple.fr", delai=3) == 200
    assert requetes == [
        ("HEAD", "vigiking-bulletin/1.0", 3),
        ("GET", "vigiking-bulletin/1.0", 3),
    ]
    with pytest.raises(ValueError):
        ver._chercher("file:///etc/passwd")


# --- Report ---------------------------------------------------------------------------


def test_the_report_lists_sections_in_order_with_their_marks():
    alertes = [
        ver.Alerte("info", "Note."),
        ver.Alerte("verifier", "À voir."),
        ver.Alerte("corriger", "Faux 1."),
        ver.Alerte("corriger", "Faux 2."),
    ]
    assert ver.rapport(alertes, "Vigiking Normand, octobre 2025") == (
        "Vigiking Normand, octobre 2025\n\n"
        "À corriger (2)\n✖ Faux 1.\n✖ Faux 2.\n\n"
        "À vérifier (1)\n⚠ À voir.\n\n"
        "Pour information (1)\nℹ Note.\n"
    )


def test_the_report_says_when_there_is_nothing_to_do():
    assert (
        ver.rapport([], "Titre")
        == "Titre\n\n✔ Rien à signaler : le bulletin est prêt.\n"
    )
    seulement_info = ver.rapport([ver.Alerte("info", "Note.")], "Titre")
    assert seulement_info == (
        "Titre\n\n✔ Rien à corriger ni à vérifier.\n\nPour information (1)\nℹ Note.\n"
    )


def test_an_unknown_alert_level_is_refused():
    with pytest.raises(ValueError):
        ver.Alerte("grave", "x")
