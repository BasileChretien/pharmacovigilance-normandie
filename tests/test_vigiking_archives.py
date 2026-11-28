"""Tests for tools/build/fetch_vigiking.py and make_vigiking_page.py (archive of Vigiking)."""

import re

import fetch_vigiking as fv
import make_vigiking_page as mp

# Same structure as https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/
PAGE = """
<main>
<article>
<header>
<h2>
<a href="https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/avril-2025/">
Avril 2025                    </a>
</h2>
</header>
<div class="content">
<p>
<p>Rappel sur les benzodiazépines et leurs risques ;<br />
Syndrome de sevrage et nécessité d&rsquo;un arrêt progressif ;</p>
</p>
</div>
<footer>
<div class="wp-block-button">
<a href="https://www.rfcrpv.fr/wp-content/uploads/2025/11/Vigiking-2025-04.pdf" class="wp-block-button__link" target="_blank">Télécharger le fichier</a>
</div>
</footer>
</article>
<article>
<header><h2><a href="https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/septembre-octobre-2018/">
Septembre – Octobre 2018 </a></h2></header>
<div class="content"><p>
</p></div>
<footer><div class="wp-block-button">
<a href="https://www.rfcrpv.fr/wp-content/uploads/2017/08/VIGIKING-2018-09-10.pdf" class="wp-block-button__link">Télécharger le fichier</a>
</div></footer>
</article>
<article>
<header><h2><a href="https://elsewhere.example/vigiking/">Mars 2018</a></h2></header>
<div class="content"><p>Un lien hors du site du réseau</p></div>
<footer><a href="https://elsewhere.example/x.pdf" class="wp-block-button__link">Télécharger</a></footer>
</article>
<article>
<header><h2><a href="https://www.rfcrpv.fr/actualites/autre-chose/">Une actualité</a></h2></header>
<div class="content"><p>Pas un numéro : pas de PDF.</p></div>
</article>
</main>
"""


def test_each_issue_keeps_its_title_month_topics_and_links():
    numeros = fv.parse_numeros(PAGE)
    assert len(numeros) == 2  # the off-site one and the one without a PDF are dropped
    avril = numeros[0]
    assert avril == {
        "titre": "Avril 2025",
        "mois": "2025-04",
        "page": "https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/avril-2025/",
        "pdf": "https://www.rfcrpv.fr/wp-content/uploads/2025/11/Vigiking-2025-04.pdf",
        "sujets": [
            "Rappel sur les benzodiazépines et leurs risques",
            "Syndrome de sevrage et nécessité d’un arrêt progressif",
        ],
    }


def test_a_double_issue_takes_its_first_month_and_may_list_no_topic():
    double = fv.parse_numeros(PAGE)[1]
    assert double["titre"] == "Septembre – Octobre 2018"
    assert double["mois"] == "2018-09"
    assert double["sujets"] == []


def test_the_table_links_each_issue_and_says_when_topics_are_missing():
    data = {
        "source": fv.SOURCE,
        "consulte_le": "2026-11-27",
        "numeros": fv.parse_numeros(PAGE),
    }
    html = mp.table(data)
    assert html.count("<tr>") == 3  # header + 2 issues
    assert (
        '<a href="https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/avril-2025/">Avril 2025</a>'
        in html
    )
    assert (
        '>PDF<span class="visually-hidden"> d’avril 2025</span></a>' in html
    )  # unique link names
    assert "<li>Rappel sur les benzodiazépines et leurs risques</li>" in html
    assert "Sommaire non indiqué sur le site du réseau" in html


def test_the_topics_column_gets_most_of_the_width():
    """Quarto shares out columns without widths evenly (33 % each)."""
    data = {"source": fv.SOURCE, "consulte_le": "2026-11-27", "numeros": fv.parse_numeros(PAGE)}
    widths = [int(w) for w in re.findall(r'<col style="width: (\d+)%">', mp.table(data))]
    assert len(widths) == 3 and sum(widths) == 100 and widths[1] == max(widths)


def test_issue_text_from_the_network_is_escaped():
    data = {
        "source": fv.SOURCE,
        "consulte_le": "2026-11-27",
        "numeros": [
            {
                "titre": "Mai 2024",
                "mois": "2024-05",
                "page": fv.SOURCE,
                "pdf": fv.SOURCE + "x.pdf",
                "sujets": ["<script>x</script>"],
            }
        ],
    }
    assert "<script>" not in mp.table(data)


def test_the_page_says_when_and_where_the_list_was_read():
    data = {
        "source": fv.SOURCE,
        "consulte_le": "2026-11-27",
        "numeros": fv.parse_numeros(PAGE),
    }
    assert "relevée le 27/11/2026" in mp.releve(data)
    assert f'href="{fv.SOURCE}"' in mp.releve(data)
    assert "2 numéros" in mp.releve(data)


def test_the_month_is_found_when_the_title_goes_on_after_the_year():
    assert fv._mois("Janvier – Février 2020 – N°38") == "2020-01"
    assert fv._mois("Sans date") is None


def _article(contenu, classe="content"):
    return (
        '<article><header><h2><a href="https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/mai-2024/">'
        f'Mai 2024</a></h2></header><div class="{classe}">{contenu}</div>'
        '<footer><div class="wp-block-button"><a href="https://www.rfcrpv.fr/wp-content/uploads/2024/06/Vigiking-2024-05.pdf" '
        'class="wp-block-button__link">Télécharger le fichier</a></div></footer></article>'
    )


def test_topics_in_separate_paragraphs_stay_separate():
    numero = fv.parse_numeros(
        _article("<p>Troubles de la pigmentation</p>\n<p>Neuropathie périphérique</p>")
    )[0]
    assert numero["sujets"] == [
        "Troubles de la pigmentation",
        "Neuropathie périphérique",
    ]


def test_the_pdf_is_the_download_button_not_a_link_inside_the_topics():
    contenu = '<p>Voir <a href="https://ansm.sante.fr/document.pdf">la lettre de l’ANSM</a> ; Autre sujet</p>'
    numero = fv.parse_numeros(_article(contenu))[0]
    assert (
        numero["pdf"]
        == "https://www.rfcrpv.fr/wp-content/uploads/2024/06/Vigiking-2024-05.pdf"
    )
    assert numero["sujets"] == ["Voir la lettre de l’ANSM", "Autre sujet"]


def test_a_content_block_with_another_class_or_a_nested_block_keeps_its_topics():
    contenu = '<div class="extrait"><p>Premier sujet</p></div><p>Second sujet</p>'
    assert fv.parse_numeros(_article(contenu, "content entry"))[0]["sujets"] == [
        "Premier sujet",
        "Second sujet",
    ]


def test_no_elision_before_h():
    assert mp._de("Hors-série 2021") == "de hors-série 2021"
    assert mp._de("Avril 2025") == "d’avril 2025"


def test_a_block_whose_class_only_starts_with_content_is_not_the_content():
    contenu = "<p>Sujet</p>"
    article = _article(contenu).replace(
        '<div class="content">',
        '<div class="content-header"><p>En-tête</p></div>'
        '<div class="entry-content-meta"><p>Méta</p></div><div class="content">',
    )
    assert fv.parse_numeros(article)[0]["sujets"] == ["Sujet"]


def test_content_among_other_classes_is_the_content():
    article = _article("<p>Sujet</p>", classe="entry content wp-block")
    assert fv.parse_numeros(article)[0]["sujets"] == ["Sujet"]
