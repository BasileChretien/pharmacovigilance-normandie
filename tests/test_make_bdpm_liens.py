"""Tests for tools/build/make_bdpm_liens.py (official notice and SmPC links, from the BDPM)."""

import make_bdpm_liens as mb

# Same columns as the BDPM files (tab-separated): CIS_bdpm.txt
SPECIALITES = "\n".join(
    "\t".join(row)
    for row in [
        [
            "68634000",
            "ADVIL 200 mg, comprimé enrobé",
            "comprimé enrobé",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/1990",
            "",
            "",
            " LAB A",
            "Non",
        ],
        [
            "60000001",
            "IBUPROFENE ARROW 200 mg, comprimé pelliculé",
            "comprimé pelliculé",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2005",
            "",
            "",
            " ARROW",
            "Non",
        ],
        [
            "60000002",
            "ADVILCAPS 400 mg, capsule molle",
            "capsule molle",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Arrêt de commercialisation",
            "01/01/2000",
            "",
            "",
            " LAB A",
            "Non",
        ],
        [
            "60000003",
            "NUROFENGEL 5 %, gel",
            "gel",
            "cutanée",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2001",
            "",
            "",
            " LAB B",
            "Non",
        ],
        [
            "60000004",
            "PARACETAMOL CODEINE ARROW 500 mg/30 mg, comprimé",
            "comprimé",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2010",
            "",
            "",
            " ARROW",
            "Non",
        ],
        [
            "60000005",
            "LEVOTHYROX 100 microgrammes, comprimé sécable",
            "comprimé sécable",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/1995",
            "",
            "",
            " LAB C",
            "Non",
        ],
        [
            "60000006",
            "ANCIEN 10 mg, comprimé",
            "comprimé",
            "orale",
            "Autorisation abrogée",
            "Procédure nationale",
            "Non commercialisée",
            "01/01/1980",
            "",
            "",
            " LAB D",
            "Non",
        ],
        [
            "60000007",
            "PREDNISOLONE ARROW 20 mg, comprimé",
            "comprimé",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2008",
            "",
            "",
            " ARROW",
            "Non",
        ],
        [
            "60000008",
            "ENTRESTO 24 mg/26 mg, comprimé pelliculé",
            "comprimé pelliculé",
            "orale",
            "Autorisation active",
            "Procédure centralisée",
            "Commercialisée",
            "01/01/2015",
            "",
            "",
            " NOVARTIS",
            "Non",
        ],
        [
            "60000009",
            "VALSARTAN ARROW 80 mg, comprimé",
            "comprimé",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2012",
            "",
            "",
            " ARROW",
            "Non",
        ],
        [
            "60000010",
            "IZILOX 400 mg/250 ml, solution pour perfusion",
            "solution pour perfusion",
            "intraveineuse",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2002",
            "",
            "",
            " BAYER",
            "Non",
        ],
        [
            "60000011",
            "MOXIFLOXACINE ARROW 400 mg, comprimé",
            "comprimé",
            "orale",
            "Autorisation active",
            "Procédure nationale",
            "Commercialisée",
            "01/01/2014",
            "",
            "",
            " ARROW",
            "Non",
        ],
    ]
)
# CIS_COMPO_bdpm.txt: CIS, element, substance code, substance, dosage, reference, SA/FT, link number
COMPOSITIONS = "\n".join(
    "\t".join(row)
    for row in [
        [
            "68634000",
            "comprimé",
            "01",
            "IBUPROFÈNE",
            "200 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        [
            "60000001",
            "comprimé",
            "01",
            "IBUPROFÈNE",
            "200 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        ["60000002", "capsule", "01", "IBUPROFÈNE", "400 mg", "une capsule", "SA", "1"],
        ["60000003", "gel", "01", "IBUPROFÈNE", "5 g", "100 g de gel", "SA", "1"],
        [
            "60000004",
            "comprimé",
            "02",
            "PARACÉTAMOL",
            "500 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        [
            "60000004",
            "comprimé",
            "03",
            "PHOSPHATE DE CODÉINE HÉMIHYDRATÉ",
            "30 mg",
            "un comprimé",
            "SA",
            "2",
        ],
        ["60000004", "comprimé", "04", "CODÉINE", "22 mg", "un comprimé", "FT", "2"],
        [
            "60000005",
            "comprimé",
            "05",
            "LÉVOTHYROXINE SODIQUE",
            "100 µg",
            "un comprimé",
            "SA",
            "1",
        ],
        [
            "60000006",
            "comprimé",
            "06",
            "ANCIENNE SUBSTANCE",
            "10 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        [
            "60000007",
            "comprimé",
            "07",
            "PREDNISOLONE",
            "20 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        [
            "60000008",
            "comprimé",
            "08",
            "SACUBITRIL VALSARTAN SODIQUE HÉMIPENTAHYDRATÉ",
            "49 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        ["60000008", "comprimé", "09", "SACUBITRIL", "24 mg", "un comprimé", "FT", "1"],
        ["60000008", "comprimé", "10", "VALSARTAN", "26 mg", "un comprimé", "FT", "1"],
        ["60000009", "comprimé", "10", "VALSARTAN", "80 mg", "un comprimé", "SA", "1"],
        [
            "60000010",
            "solution",
            "11",
            "CHLORHYDRATE DE MOXIFLOXACINE",
            "400 mg",
            "250 ml",
            "SA",
            "1",
        ],
        [
            "60000011",
            "comprimé",
            "11",
            "CHLORHYDRATE DE MOXIFLOXACINE",
            "400 mg",
            "un comprimé",
            "SA",
            "1",
        ],
    ]
)
# CIS_GENER_bdpm.txt: group, label, CIS, type (0 = princeps), sort
GENERIQUES = "\n".join(
    "\t".join(row)
    for row in [
        ["1", "IBUPROFENE 200 mg - ADVIL 200 mg, comprimé", "68634000", "0", "1"],
        ["1", "IBUPROFENE 200 mg - ADVIL 200 mg, comprimé", "60000001", "1", "2"],
        ["2", "IBUPROFENE 400 mg - ADVILCAPS 400 mg, capsule", "60000002", "0", "1"],
        ["3", "IBUPROFENE 5 % - NUROFENGEL 5 %, gel", "60000003", "0", "1"],
        ["4", "VALSARTAN 24 mg/26 mg - ENTRESTO", "60000008", "0", "1"],
        [
            "5",
            "MOXIFLOXACINE 400 mg - IZILOX, solution pour perfusion",
            "60000010",
            "0",
            "1",
        ],
    ]
)


def _base():
    return mb.Base.from_texts(SPECIALITES, COMPOSITIONS, GENERIQUES)


def test_names_are_compared_without_case_or_accents():
    assert mb.normalise("  IBUPROFÈNE   Lysine ") == "ibuprofene lysine"


def test_the_marketed_oral_princeps_with_that_substance_alone_is_chosen():
    choix = _base().choisir("ibuprofène")
    assert choix["cis"] == "68634000"
    assert choix["nom"] == "ADVIL 200 mg, comprimé enrobé"
    assert choix["princeps"] is True
    assert (
        choix["nb"] == 3
    )  # Advil, Ibuprofène Arrow, Nurofengel; not Advilcaps (no longer marketed)


def test_a_salt_matches_its_substance_but_a_longer_name_does_not():
    base = _base()
    assert base.choisir("lévothyroxine")["cis"] == "60000005"
    assert base.choisir("prednisolone")["cis"] == "60000007"
    assert base.choisir("predniso") is None
    assert base.choisir("prednisone") is None


def test_a_salt_written_before_its_substance_matches_too():
    assert mb._matches("tartrate de zolpidem", "zolpidem")
    assert mb._matches(mb.normalise("BÉSILATE D’AMLODIPINE"), "amlodipine")
    assert mb._matches("phosphate de codeine hemihydrate", "codeine")
    assert not mb._matches("tartrate de zolpidemine", "zolpidem")
    assert not mb._matches("acide de", "de")


def test_a_combined_salt_with_two_active_parts_is_a_combination_not_the_substance_alone():
    choix = _base().choisir("valsartan")
    assert (
        choix["cis"] == "60000009"
    )  # Valsartan Arrow, not Entresto (sacubitril/valsartan)
    assert choix["association"] is False


def test_an_oral_form_comes_before_the_princeps_given_by_infusion():
    assert _base().choisir("moxifloxacine")["cis"] == "60000011"


def test_a_substance_sold_only_in_combination_falls_back_to_a_combination():
    choix = _base().choisir("codéine")
    assert choix["cis"] == "60000004"
    assert choix["association"] is True


def test_a_substance_never_marketed_gives_nothing():
    assert _base().choisir("ancienne substance") is None


def test_cited_products_get_their_marketing_status():
    base = _base()
    assert base.statut("68634000") == {
        "nom": "ADVIL 200 mg, comprimé enrobé",
        "etat": "Commercialisée",
    }
    assert base.statut("60000006")["etat"] == "Non commercialisée"
    assert base.statut("99999999") is None


def test_pages_give_their_substances_and_the_products_they_cite(tmp_path):
    (tmp_path / "medicaments").mkdir()
    (tmp_path / "medicaments" / "ains.qmd").write_text(
        "---\ntitle: AINS\nsubstances: [ibuprofène, codéine]\nsources:\n"
        '  - titre: "BDPM, ADVIL"\n'
        '    url: "https://base-donnees-publique.medicaments.gouv.fr/medicament/68634000/extrait"\n'
        "---\n\nTexte.\n",
        encoding="utf-8",
    )
    (tmp_path / "autre.qmd").write_text(
        "---\ntitle: Autre\n---\n\nVoir https://base-donnees-publique.medicaments.gouv.fr/medicament/60000006/extrait\n",
        encoding="utf-8",
    )
    substances, cites, en_sources = mb.lire_pages(tmp_path)
    assert substances == {"medicaments/ains.qmd": ["ibuprofène", "codéine"]}
    assert cites == {"68634000": ["medicaments/ains.qmd"], "60000006": ["autre.qmd"]}
    assert en_sources == {"68634000": ["medicaments/ains.qmd"]}


def test_report_lists_unknown_substances_and_products_no_longer_marketed():
    data = mb.construire(
        _base(),
        {"medicaments/ains.qmd": ["ibuprofène", "inconnue"]},
        {"68634000": ["a.qmd"], "60000006": ["b.qmd"], "99999999": ["c.qmd"]},
        "2026-11-20",
    )
    assert data["mis_a_jour"] == "2026-11-20"
    assert data["substances"]["ibuprofène"]["cis"] == "68634000"
    assert "inconnue" not in data["substances"]
    problemes = mb.rapport(
        data,
        {"medicaments/ains.qmd": ["ibuprofène", "inconnue"]},
        {"60000006": ["b.qmd"], "99999999": ["c.qmd"]},
    )
    assert any("inconnue" in p for p in problemes)
    assert any("60000006" in p and "Non commercialisée" in p for p in problemes)
    assert any("99999999" in p for p in problemes)
    assert not any("68634000" in p for p in problemes)


def test_update_date_of_the_products_file_is_read_from_the_download_page():
    # Same markup as https://base-donnees-publique.medicaments.gouv.fr/telechargement
    page = (
        '<a class="fr-download__link" href="/download/file/CIS_CIP_bdpm.txt" download>'
        "Fichier des présentations (Date de mise à jour : 27/11/2026, 4052 Ko) </a>"
        '<a class="fr-download__link" href="/download/file/CIS_bdpm.txt" role="link" '
        'aria-label="Cliquez ici" download=\'CIS_bdpm.txt\'> <span aria-hidden="true"></span> '
        "Fichier des spécialités (Date de mise à jour : 20/11/2026, 3093 Ko) </a>"
    )
    assert mb.date_specialites(page) == "2026-11-20"


def test_a_missing_files_date_is_reported():
    data = mb.construire(_base(), {}, {}, None)
    assert any("date" in p for p in mb.rapport(data, {}, {}))
    dated = mb.construire(_base(), {}, {}, "2026-11-20")
    assert mb.rapport(dated, {}, {}) == []


def test_an_inverted_salt_reads_as_the_usual_name():
    assert mb.normalise("SODIUM (VALPROATE DE)") == "valproate de sodium"
    assert mb._matches(
        mb.normalise("SODIUM (VALPROATE DE)"), mb.normalise("valproate de sodium")
    )
    assert mb.normalise("AMMONIUM (CHLORURE D')") == "chlorure d'ammonium"


def _pages(listed: list[str], cited: list[str]) -> dict:
    en_sources = {cis: ["medicaments/p.qmd"] for cis in cited}
    data = mb.construire(
        _base(), {"medicaments/p.qmd": listed}, en_sources, "2026-11-20", en_sources
    )
    return data["pages"]


def test_a_page_citing_a_marketed_product_of_the_substance_alone_gets_it_as_example():
    pages = _pages(["ibuprofène"], ["60000001"])  # IBUPROFENE ARROW, cited in sources
    assert pages == {
        "medicaments/p.qmd": {
            "ibuprofène": {
                "cis": "60000001",
                "nom": "IBUPROFENE ARROW 200 mg, comprimé pelliculé",
                "princeps": False,
                "association": False,
            }
        }
    }


def test_a_page_with_its_own_example_leaves_the_site_wide_one_unchanged():
    cites = {"60000001": ["medicaments/p.qmd"]}
    data = mb.construire(
        _base(), {"medicaments/p.qmd": ["ibuprofène"]}, cites, None, cites
    )
    assert data["pages"]["medicaments/p.qmd"]["ibuprofène"]["cis"] == "60000001"
    assert data["substances"]["ibuprofène"]["cis"] == "68634000"


def test_a_cited_product_withdrawn_or_in_combination_is_not_an_example():
    assert _pages(["ibuprofène"], ["60000002"]) == {}  # ADVILCAPS, not marketed
    # ENTRESTO: valsartan in combination.
    assert _pages(["valsartan"], ["60000008"]) == {}


def test_a_cited_product_that_is_already_the_example_adds_nothing():
    assert _pages(["ibuprofène"], ["68634000"]) == {}


def test_among_several_cited_products_the_usual_order_decides():
    # Oral before skin gel, whatever the citing order.
    pages = _pages(["ibuprofène"], ["60000003", "60000001"])
    assert pages["medicaments/p.qmd"]["ibuprofène"]["cis"] == "60000001"


def test_an_inverted_salt_followed_by_another_word_reads_the_usual_way_too():
    assert (
        mb.normalise("CODÉINE (PHOSPHATE DE) HÉMIHYDRATÉ")
        == "phosphate de codeine hemihydrate"
    )
    assert (
        mb.normalise("BENDAMUSTINE (CHLORHYDRATE DE) MONOHYDRATÉ")
        == "chlorhydrate de bendamustine monohydrate"
    )
    assert mb._matches(mb.normalise("CODÉINE (PHOSPHATE DE) HÉMIHYDRATÉ"), "codeine")


def test_a_plant_extract_with_a_second_parenthesis_is_left_as_written():
    assert (
        mb.normalise("AUBÉPINE (EXTRAIT D') (FLUIDE)")
        == "aubepine (extrait d') (fluide)"
    )


def test_only_a_product_cited_in_the_sources_can_be_the_page_example(tmp_path):
    (tmp_path / "medicaments").mkdir()
    (tmp_path / "medicaments" / "ains.qmd").write_text(
        "---\ntitle: AINS\nsubstances: [ibuprofène]\nsources:\n"
        '  - titre: "ANSM"\n'
        '    url: "https://ansm.sante.fr/"\n'
        "---\n\nÀ éviter : https://base-donnees-publique.medicaments.gouv.fr/medicament/60000001/extrait\n",
        encoding="utf-8",
    )
    substances, cites, en_sources = mb.lire_pages(tmp_path)
    assert en_sources == {}
    data = mb.construire(_base(), substances, cites, "2026-11-20", en_sources)
    assert data["pages"] == {}
    # The product named in the text is still checked for its marketing status.
    assert data["cites"]["60000001"]["etat"] == mb.COMMERCIALISEE


def test_every_page_that_lists_substances_is_named_for_the_filter():
    data = mb.construire(
        _base(),
        {"medicaments/b.qmd": ["ibuprofène"], "medicaments/a.qmd": ["inconnue"]},
        {},
        "2026-11-20",
    )
    assert data["pages_lues"] == ["medicaments/a.qmd", "medicaments/b.qmd"]


def test_the_bulletin_folder_is_not_read(tmp_path):
    (tmp_path / "bulletin" / "numeros").mkdir(parents=True)
    (tmp_path / "bulletin" / "numeros" / "n.qmd").write_text(
        "---\ntitle: N\nsubstances: [ibuprofène]\n---\n", encoding="utf-8"
    )
    assert mb.lire_pages(tmp_path) == ({}, {}, {})
