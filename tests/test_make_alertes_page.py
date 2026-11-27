"""Tests for tools/build/make_alertes_page.py (the lists of the official alerts feed)."""

import make_alertes_page as mp

ANSM = {
    "source": "https://ansm.sante.fr/informations-de-securite/",
    "releve_le": "2026-11-30",
    "alertes": [
        {
            "titre": "Respreeza : risque d’impossibilité d’administration",
            "url": "https://ansm.sante.fr/informations-de-securite/respreeza",
            "publie_le": "2026-11-09",
            "mis_a_jour_le": None,
            "produit": "Médicaments",
            "public": "Information destinée aux pharmaciens hospitaliers",
        },
        {
            "titre": "Tegretol <script>alert(1)</script> & co",
            "url": "https://ansm.sante.fr/informations-de-securite/tegretol",
            "publie_le": "2026-01-06",
            "mis_a_jour_le": "2026-05-04",
            "produit": "Médicaments",
            "public": None,
        },
    ],
}

EMA = {
    "source": "https://www.ema.europa.eu/en/committees/pharmacovigilance-risk-assessment-committee-prac",
    "releve_le": "2026-11-23",
    "alertes": [
        {
            "titre": "Meeting highlights from the PRAC 26 - 29 October 2026",
            "resume": "PRAC starts review of Deanxit",
            "url": "https://www.ema.europa.eu/en/news/prac-26-29-october-2026",
            "publie_le": "2026-10-30",
        }
    ],
}


def test_ansm_list_shows_date_product_title_link_and_audience():
    html = mp.liste(ANSM, "ansm")
    assert html.count("<li") == 2
    assert '<time datetime="2026-11-09">09/11/2026</time>' in html
    assert '<a href="https://ansm.sante.fr/informations-de-securite/respreeza">' in html
    assert "Information destinée aux pharmaciens hospitaliers" in html
    assert 'mis à jour le <time datetime="2026-05-04">04/05/2026</time>' in html


def test_titles_from_the_sites_are_escaped():
    html = mp.liste(ANSM, "ansm")
    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; co" in html


def test_each_list_says_when_and_where_it_was_read():
    ansm = mp.liste(ANSM, "ansm")
    assert 'Liste relevée le <time datetime="2026-11-30">30/11/2026</time>' in ansm
    assert 'href="https://ansm.sante.fr/informations-de-securite/"' in ansm
    ema = mp.liste(EMA, "ema")
    assert 'Liste relevée le <time datetime="2026-11-23">23/11/2026</time>' in ema


def test_ema_titles_and_summaries_are_marked_as_english():
    html = mp.liste(EMA, "ema")
    assert '<p class="fil-titre" lang="en">' in html
    assert '<p class="fil-resume" lang="en">PRAC starts review of Deanxit</p>' in html


def test_a_source_never_read_says_so_instead_of_an_empty_list():
    html = mp.liste(None, "ema")
    assert "<ul" not in html
    assert "pas encore été relevée" in html
