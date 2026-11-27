"""Tests for tools/build/make_crpv_page.py (table of the 30 centres and data for the finder)."""

import json

import make_crpv_page as mp

DATA = {
    "source": "https://ansm.sante.fr/page/liste-des-centres-regionaux-de-pharmacovigilance",
    "mis_a_jour": "2026-09-14",
    "consulte_le": "2026-11-27",
    "centres": [
        {
            "nom": "Centre de Caen",
            "departements": [
                {
                    "code": "14",
                    "nom": "Calvados",
                    "precision": None,
                    "arrondissements": None,
                },
                {
                    "code": "50",
                    "nom": "Manche",
                    "precision": None,
                    "arrondissements": None,
                },
            ],
            "telephone": "02 31 06 46 72",
            "courriel": "pharmacovigilance@chu-caen.fr",
            "site": "http://www.chu-caen.fr/pharmacologie.html",
        },
        {
            "nom": "Centre de Paris Cochin - Port Royal",
            "departements": [
                {
                    "code": "75",
                    "nom": "Paris",
                    "precision": None,
                    "arrondissements": [1, 6],
                },
                {
                    "code": "78",
                    "nom": "Yvelines",
                    "precision": "Sud",
                    "arrondissements": None,
                },
            ],
            "telephone": "01 58 41 34 79",
            "courriel": "pharmacovigilance.hupc@aphp.fr",
            "site": None,
        },
    ],
}


def test_departments_are_readable_with_paris_arrondissements_and_split_parts():
    assert mp.departements_label(DATA["centres"][0]) == "Calvados (14), Manche (50)"
    assert (
        mp.departements_label(DATA["centres"][1])
        == "Paris (1er, 6e arrondissements), Yvelines, partie sud (78)"
    )


def test_table_has_one_row_per_centre_with_phone_email_and_site():
    html = mp.table(DATA)
    assert html.count("<tr>") == 3  # header + 2 centres
    assert 'href="tel:+33231064672"' in html
    assert "02\u00a031\u00a006\u00a046\u00a072" in html  # non-breaking spaces in the number
    assert 'href="mailto:pharmacovigilance@chu-caen.fr"' in html
    assert ">chu-caen.fr</a>" in html  # the site is named by its domain
    assert "&mdash;" in html  # no site: a dash, not an empty link


def test_data_block_holds_the_centres_and_cannot_close_its_script_tag():
    tricky = {**DATA, "centres": [{**DATA["centres"][0], "nom": "</script><b>x</b>"}]}
    block = mp.data_block(tricky)
    assert block.count("</script>") == 1  # only the real closing tag
    payload = block.split(">", 1)[1].rsplit("</script>", 1)[0]
    assert json.loads(payload)["centres"][0]["nom"] == "</script><b>x</b>"
