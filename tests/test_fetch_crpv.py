"""Tests for tools/build/fetch_crpv.py (the ANSM list of regional pharmacovigilance centres)."""

import fetch_crpv as fc

# Same structure as https://ansm.sante.fr/page/liste-des-centres-regionaux-de-pharmacovigilance
FIXTURE = """
<h1>Liste des centres</h1><p>PUBLI&Eacute; LE 09/10/2020 - MIS &Agrave; JOUR LE 14/09/2026</p>
<div class="accordion-item">
  <a class="accordion-heading" href="#"><span>&nbsp;</span> Centre de Caen </a>
  <div class="accordion-body"><ul>
    <li>D&eacute;partements concern&eacute;s :<ul><li>Calvados (14)</li><li>Manche (50)</li><li>Orne (61)</li></ul></li>
    <li>Centre R&eacute;gional de Pharmacovigilance<br />14033 CAEN CEDEX 9</li>
    <li><strong>Mme le Dr Pr&eacute;nom Nom</strong><br />T&eacute;l&eacute;phone : 02.31.06.46.72&nbsp;<br />T&eacute;l&eacute;copie : 02.31.06.46.73<br />e-mail :&nbsp;<a href="mailto:pharmacovigilance@chu-caen.fr">pharmacovigilance@chu-caen.fr</a></li>
    <li><strong><a href="http://www.chu-caen.fr/pharmacologie.html">Acceder au site Internet</a></strong></li>
  </ul></div>
</div>
<div class="accordion-item">
  <a class="accordion-heading" href="#"><span>&nbsp;</span> Centre de Paris HEGP </a>
  <div class="accordion-body"><ul>
    <li>D&eacute;partements concern&eacute;s :<ul><li>Paris 14-15-16 (750014-75015-75016)</li><li>Yvelines Nord (78)</li><li>Hauts-de-Seine (92)</li></ul></li>
    <li><strong>M. le Dr Pr&eacute;nom Nom</strong><br />T&eacute;l&eacute;phone : 01 56.09.39.88<br />e-mail : <a href="mailto:crpv.hegp@aphp.fr">crpv.hegp@aphp.fr</a></li>
  </ul></div>
</div>
<div class="accordion-item">
  <a class="accordion-heading" href="#"><span>&nbsp;</span> Centre de Saint-Etienne </a>
  <div class="accordion-body"><ul>
    <li>D&eacute;partement concern&eacute; :<ul><li>Loire (42)</li></ul></li>
    <li>Guadeloupe (971) is not here: this line is an address, not a department</li>
    <li>T&eacute;l&eacute;phone : 04.77.12.77.37<br />e-mail : <a href="mailto:pharmacovigilance@chu-st-etienne.fr">x</a></li>
  </ul></div>
</div>
"""


def test_update_date_of_the_list_is_read():
    assert fc.parse_update_date(FIXTURE) == "2026-09-14"


def test_each_centre_gets_its_departments_phone_email_and_site_but_no_person_name():
    centres = fc.parse_centres(FIXTURE)
    assert [c["nom"] for c in centres] == [
        "Centre de Caen",
        "Centre de Paris HEGP",
        "Centre de Saint-Etienne",
    ]
    caen = centres[0]
    assert [d["code"] for d in caen["departements"]] == ["14", "50", "61"]
    assert caen["telephone"] == "02 31 06 46 72"
    assert caen["courriel"] == "pharmacovigilance@chu-caen.fr"
    assert caen["site"] == "http://www.chu-caen.fr/pharmacologie.html"
    assert "Nom" not in str(caen)  # the head of the centre is not kept


def test_paris_arrondissements_come_from_the_numbers_not_the_mistyped_codes():
    hegp = fc.parse_centres(FIXTURE)[1]
    paris = next(d for d in hegp["departements"] if d["code"] == "75")
    assert paris["arrondissements"] == [14, 15, 16]


def test_a_split_department_keeps_its_part():
    hegp = fc.parse_centres(FIXTURE)[1]
    yvelines = next(d for d in hegp["departements"] if d["code"] == "78")
    assert yvelines["precision"] == "Nord"
    assert yvelines["nom"] == "Yvelines"


def test_singular_heading_and_codes_of_every_shape():
    assert [d["code"] for d in fc.parse_centres(FIXTURE)[2]["departements"]] == ["42"]
    assert fc.parse_departement("Corse-du-Sud (2A)")["code"] == "2A"
    assert fc.parse_departement("Guadeloupe (971)")["code"] == "971"
    assert fc.parse_departement("Val d'Oise (95)")["nom"] == "Val d'Oise"


def test_email_href_is_decoded_so_an_encoded_trailing_space_is_dropped():
    page = FIXTURE.replace(
        'href="mailto:crpv.hegp@aphp.fr"', 'href="mailto:crpv.hegp@aphp.fr%20"'
    )
    assert fc.parse_centres(page)[1]["courriel"] == "crpv.hegp@aphp.fr"


def test_missing_site_is_none():
    assert fc.parse_centres(FIXTURE)[1]["site"] is None
