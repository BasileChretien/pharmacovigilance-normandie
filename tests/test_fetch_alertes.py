"""Tests for tools/build/fetch_alertes.py (the official alerts feed: ANSM and EMA)."""

import fetch_alertes as fa

# Same structure as https://ansm.sante.fr/informations-de-securite/ (drug risks filter)
ANSM = """
<div class="article-list">
<article class="article-item article-security" role="article">
  <a href="/informations-de-securite/respreeza-risque-dimpossibilite-dadministration" title="x">
    <span class="article-category">
        RISQUES MEDICAMENTEUX
    </span>
    <span class="article-health-product">
                        M&eacute;dicaments
                </span>
    <span class="article-date">
                    PUBLI&Eacute; LE 09/11/2026

    </span>
    <span class="article-title h5">Respreeza (alpha-1-antitrypsine humaine) : risque d&rsquo;impossibilit&eacute; d&rsquo;administration</span>
    <span class="article-content">
        Information destin&eacute;e aux pharmaciens hospitaliers
    </span>
  </a>
</article>
<article class="article-item article-security" role="article">
  <a href="/informations-de-securite/tegretol-20-mg-ml-suspension-buvable" title="x">
    <span class="article-category">RISQUES MEDICAMENTEUX</span>
    <span class="article-health-product">M&eacute;dicaments</span>
    <span class="article-date">
                    PUBLI&Eacute; LE 06/01/2026
        - MIS &Agrave; JOUR LE 04/05/2026
    </span>
    <span class="article-title h5">Tegretol 20 mg/ml suspension buvable : <b>restriction</b> chez les nouveau-n&eacute;s</span>
    <span class="article-content"></span>
  </a>
</article>
<article class="article-item article-security" role="article">
  <a href="https://elsewhere.example/informations-de-securite/piege" title="x">
    <span class="article-health-product">M&eacute;dicaments</span>
    <span class="article-date">PUBLI&Eacute; LE 01/01/2026</span>
    <span class="article-title h5">Lien hors du site de l'ANSM</span>
  </a>
</article>
</div>
"""

# Same structure as https://www.ema.europa.eu/en/committees/pharmacovigilance-risk-assessment-committee-prac
EMA = """
<article class="node ema-news ema-embedded-listing listing-item card"><div class='row'><div class='col'>
  <img src="x.webp" alt="Magnifying glass examining capsules, tablets and syringes."/>
  <div class="card-body p-0 pb-md-0 pb-3">
    <h3 class="teaser-title card-title bcl-heading"><a class="standalone" href="/en/news/meeting-highlights-pharmacovigilance-risk-assessment-committee-prac-26-29-october-2026">Meeting highlights from the Pharmacovigilance Risk Assessment Committee (PRAC) 26 - 29 October 2026</a></h3>
      <div class="card-text mb-3">  <p>PRAC starts review of depression and anxiety medicine Deanxit</p>
</div><div class="metadata me-n3"><div class="metadata-item text-muted me-3">      30 October 2026</div></div></div></div></div></article>
<article class="node ema-news ema-embedded-listing listing-item card"><div class='row'><div class='col'>
  <div class="card-body p-0 pb-md-0 pb-3">
    <h3 class="teaser-title card-title bcl-heading"><a class="standalone" href="/en/news/meeting-highlights-pharmacovigilance-risk-assessment-committee-prac-6-9-july-2026">Meeting highlights from the Pharmacovigilance Risk Assessment Committee (PRAC) 6-9 July 2026</a></h3>
      <div class="card-text mb-3">  <p>PRAC agrees new safety information on desogestrel- and etonogestrel-containing contraceptives</p>
</div><div class="metadata me-n3"><div class="metadata-item text-muted me-3">      10 July 2026</div></div></div></div></div></article>
<article class="node ema-news ema-embedded-listing listing-item card">
    <h3 class="teaser-title card-title"><a class="standalone" href="javascript:alert(1)">Not an EMA page</a></h3>
    <div class="metadata-item text-muted me-3">1 July 2026</div></article>
"""


def test_ansm_items_keep_title_date_product_audience_and_an_absolute_link():
    items = fa.parse_ansm(ANSM)
    assert len(items) == 2  # the off-site link is dropped
    first = items[0]
    assert first == {
        "titre": "Respreeza (alpha-1-antitrypsine humaine) : risque d’impossibilité d’administration",
        "url": "https://ansm.sante.fr/informations-de-securite/respreeza-risque-dimpossibilite-dadministration",
        "publie_le": "2026-11-09",
        "mis_a_jour_le": None,
        "produit": "Médicaments",
        "public": "Information destinée aux pharmaciens hospitaliers",
    }


def test_ansm_update_date_is_kept_and_markup_in_a_title_becomes_text():
    second = fa.parse_ansm(ANSM)[1]
    assert second["publie_le"] == "2026-01-06"
    assert second["mis_a_jour_le"] == "2026-05-04"
    assert (
        second["titre"]
        == "Tegretol 20 mg/ml suspension buvable : restriction chez les nouveau-nés"
    )
    assert second["public"] is None


def test_ema_prac_highlights_keep_title_summary_date_and_link():
    items = fa.parse_ema(EMA)
    assert len(items) == 2  # the javascript: link is dropped
    assert items[0] == {
        "titre": "Meeting highlights from the Pharmacovigilance Risk Assessment Committee (PRAC) 26 - 29 October 2026",
        "resume": "PRAC starts review of depression and anxiety medicine Deanxit",
        "url": "https://www.ema.europa.eu/en/news/meeting-highlights-pharmacovigilance-risk-assessment-committee-prac-26-29-october-2026",
        "publie_le": "2026-10-30",
    }
    assert items[1]["publie_le"] == "2026-07-10"


def _fetcher(pages):
    def fetch(url):
        page = pages[url]
        if isinstance(page, Exception):
            raise page
        return page

    return fetch


def test_refresh_replaces_both_lists_and_dates_them():
    pages = {fa.SOURCES["ansm"]["url"]: ANSM * 3, fa.SOURCES["ema"]["url"]: EMA}
    data, errors = fa.refresh({}, _fetcher(pages), "2026-11-30")
    assert errors == []
    assert data["ansm"]["releve_le"] == "2026-11-30"
    assert len(data["ansm"]["alertes"]) == 6
    assert data["ema"]["releve_le"] == "2026-11-30"
    assert data["ema"]["source"] == fa.SOURCES["ema"]["url"]


def test_a_site_that_fails_keeps_its_previous_list_and_date():
    previous = {
        "ansm": {
            "source": "s",
            "releve_le": "2026-11-23",
            "alertes": [{"titre": "ancienne"}],
        },
    }
    pages = {
        fa.SOURCES["ansm"]["url"]: OSError("timeout"),
        fa.SOURCES["ema"]["url"]: EMA,
    }
    data, errors = fa.refresh(previous, _fetcher(pages), "2026-11-30")
    assert data["ansm"] == previous["ansm"]
    assert data["ema"]["releve_le"] == "2026-11-30"
    assert len(errors) == 1 and errors[0].startswith("ansm")


def test_a_page_that_has_changed_shape_is_an_error_not_an_empty_list():
    pages = {
        fa.SOURCES["ansm"]["url"]: "<html>nouvelle maquette</html>",
        fa.SOURCES["ema"]["url"]: EMA,
    }
    data, errors = fa.refresh({}, _fetcher(pages), "2026-11-30")
    assert "ansm" not in data
    assert errors and "ansm" in errors[0]


def test_lists_are_capped():
    pages = {fa.SOURCES["ansm"]["url"]: ANSM * 20, fa.SOURCES["ema"]["url"]: EMA * 5}
    data, _ = fa.refresh({}, _fetcher(pages), "2026-11-30")
    assert len(data["ansm"]["alertes"]) == fa.SOURCES["ansm"]["garder"]
    assert len(data["ema"]["alertes"]) == fa.SOURCES["ema"]["garder"]
