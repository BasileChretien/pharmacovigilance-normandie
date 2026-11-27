"""Tests for tools/build/make_openmedic.py (reimbursed medicines in Normandy vs France)."""

import gzip

import make_openmedic as mo

# Same columns as NB_2025_atc5_age_sexe_reg.CSV (Open Medic, Assurance Maladie)
LIGNES_CSV = [
    "ATC5;l_atc5;age;sexe;BEN_REG;nbc;REM;BSE;BOITES",
    # Benzodiazepine (N05BA) in Normandy (28) and in another region (11)
    "N05BA12;ALPRAZOLAM;20;2;28;10;1,00;2,00;1 000",
    "N05BA12;ALPRAZOLAM;60;2;28;10;1,00;2,00;3000",
    "N05BA12;ALPRAZOLAM;20;2;11;10;1,00;2,00;2000",
    # Z-drug (N05CF) in the same group
    "N05CF02;ZOLPIDEM;60;1;28;10;1,00;2,00;500",
    # Unknown age or sex: in the crude rate, not in the standardised one
    "N05BA12;ALPRAZOLAM;99;2;28;10;1,00;2,00;100",
    "N05BA12;ALPRAZOLAM;60;9;11;10;1,00;2,00;50",
    # Not in any group
    "A01AA01;SODIUM FLUORURE;0;1;28;10;1,00;2,00;9999",
]
CSV = "\n".join(LIGNES_CSV)


def _write(tmp_path):
    path = tmp_path / "om.csv.gz"
    with gzip.open(path, "wt", encoding="cp1252") as f:
        f.write(CSV)
    return path


def test_boxes_are_summed_by_group_place_sex_and_age(tmp_path):
    boites = mo.lire_openmedic(
        _write(tmp_path), {"benzodiazepines": ("N05BA", "N05CD", "N05CF")}
    )
    assert (
        boites[("benzodiazepines", "28", "2", "20")] == 1000
    )  # thousands separator read
    assert boites[("benzodiazepines", "28", "1", "60")] == 500
    assert boites[("benzodiazepines", "FR", "2", "20")] == 3000  # France = every region
    assert boites[("benzodiazepines", "28", "2", "99")] == 100
    assert not any(k[0] != "benzodiazepines" for k in boites)


def test_five_year_bands_add_up_to_the_three_open_medic_age_groups():
    assert mo.tranche("Y_LT5") == "0" and mo.tranche("Y15T19") == "0"
    assert mo.tranche("Y20T24") == "20" and mo.tranche("Y55T59") == "20"
    assert mo.tranche("Y60T64") == "60" and mo.tranche("Y_GE95") == "60"
    assert mo.tranche("_T") is None


def _obs(geo, year, sex, age, value):
    return {
        "dimensions": {
            "GEO": geo,
            "TIME_PERIOD": str(year),
            "SEX": sex,
            "AGE": age,
            "EP_MEASURE": "POP_JAN_1ST",
        },
        "measures": {"OBS_VALUE_NIVEAU": {"value": value}},
    }


def test_population_is_the_mid_year_mean_of_two_first_januaries():
    obs = [
        _obs("2026-REG-28", 2025, "F", "Y20T24", 100),
        _obs("2026-REG-28", 2025, "F", "Y25T29", 100),
        _obs("2026-REG-28", 2026, "F", "Y20T24", 120),
        _obs("2026-REG-28", 2026, "F", "Y25T29", 120),
        _obs("2026-REG-28", 2025, "_T", "_T", 999),  # totals are ignored
    ]
    pop = mo.population(obs, 2025, {"2026-REG-28": "28"})
    assert pop == {("28", "2", "20"): 220.0}  # (200 + 240) / 2


def test_direct_standardisation_on_the_french_population():
    # Normandy: 2 strata with rates 10 and 40 per person; France: rates 10 and 20.
    boites = {
        ("g", "28", "2", "20"): 100,
        ("g", "28", "2", "60"): 400,
        ("g", "FR", "2", "20"): 1000,
        ("g", "FR", "2", "60"): 2000,
    }
    pop = {
        ("28", "2", "20"): 10,
        ("28", "2", "60"): 10,
        ("FR", "2", "20"): 100,
        ("FR", "2", "60"): 100,
    }
    # Standard: France, half of each stratum -> Normandy (10*0.5 + 40*0.5) * 1000 = 25 000 per 1000
    assert mo.taux_standardise(boites, pop, "g", "28") == 25000.0
    assert mo.taux_standardise(boites, pop, "g", "FR") == 15000.0


def test_crude_rate_counts_every_box_including_unknown_age_or_sex():
    boites = {("g", "28", "2", "20"): 100, ("g", "28", "9", "99"): 50}
    pop = {("28", "1", "20"): 50, ("28", "2", "20"): 50}
    assert (
        mo.taux_brut(boites, pop, "g", "28") == 1500.0
    )  # 150 boxes / 100 people * 1000


def test_each_group_gets_normandy_france_and_the_gap(tmp_path):
    boites = mo.lire_openmedic(
        _write(tmp_path), {"benzodiazepines": ("N05BA", "N05CD", "N05CF")}
    )
    pop = {
        (geo, s, a): 1000.0
        for geo in ("28", "FR")
        for s in ("1", "2")
        for a in ("0", "20", "60")
    }
    groupes = [
        {
            "cle": "benzodiazepines",
            "libelle": "Benzodiazépines",
            "atc": ["N05BA", "N05CD", "N05CF"],
            "fiche": None,
        }
    ]
    lignes = mo.resultats(boites, pop, groupes)
    ligne = lignes[0]
    assert ligne["normandie"]["boites"] == 4600
    assert ligne["france"]["boites"] == 6650
    expected_gap = round(
        100
        * (
            ligne["normandie"]["taux_standardise"] / ligne["france"]["taux_standardise"]
            - 1
        )
    )
    assert ligne["ecart_pct"] == expected_gap


# --- rendering ------------------------------------------------------------------

LIGNES = [
    {
        "cle": "ains",
        "libelle": "AINS <test>",
        "atc": ["M01A"],
        "fiche": "medicaments/classes/ains.qmd",
        "normandie": {"boites": 2000000, "taux_brut": 605.9, "taux_standardise": 609.6},
        "france": {"boites": 42000000, "taux_brut": 620.0, "taux_standardise": 622.4},
        "ecart_pct": -2,
    },
    {
        "cle": "opioides",
        "libelle": "Antalgiques opioïdes",
        "atc": ["N02A"],
        "fiche": "medicaments/classes/opioides.qmd",
        "normandie": {
            "boites": 4200000,
            "taux_brut": 1274.1,
            "taux_standardise": 1248.6,
        },
        "france": {"boites": 61000000, "taux_brut": 890.0, "taux_standardise": 889.3},
        "ecart_pct": 40,
    },
    {
        "cle": "corticoides",
        "libelle": "Corticoïdes",
        "atc": ["H02AB"],
        "fiche": None,
        "normandie": {"boites": 1600000, "taux_brut": 487.4, "taux_standardise": 479.5},
        "france": {"boites": 33000000, "taux_brut": 480.0, "taux_standardise": 481.6},
        "ecart_pct": 0,
    },
    {
        "cle": "antidepresseurs",
        "libelle": "Antidépresseurs",
        "atc": ["N06A"],
        "fiche": None,
        "normandie": {
            "boites": 5400000,
            "taux_brut": 1639.3,
            "taux_standardise": 1621.7,
        },
        "france": {"boites": 87000000, "taux_brut": 1270.0, "taux_standardise": 1272.6},
        "ecart_pct": 27,
    },
]


def test_numbers_are_written_the_french_way():
    assert mo.fr_nombre(1248.6) == "1&nbsp;248,6"
    assert mo.fr_nombre(4200000, 0) == "4&nbsp;200&nbsp;000"
    assert mo.fr_ecart(40) == "+40&nbsp;%"
    assert mo.fr_ecart(-2) == "&minus;2&nbsp;%"
    assert mo.fr_ecart(0) == "0&nbsp;%"


def test_the_chart_ranks_groups_by_gap_with_a_bar_each_side_of_france():
    html = mo.graphique(LIGNES, 2025)
    noms = [
        n
        for n in (
            "Antalgiques opioïdes",
            "Antidépresseurs",
            "Corticoïdes",
            "AINS &lt;test&gt;",
        )
        if n in html
    ]
    assert noms == [
        "Antalgiques opioïdes",
        "Antidépresseurs",
        "Corticoïdes",
        "AINS &lt;test&gt;",
    ]
    assert (
        html.index("Antalgiques opioïdes")
        < html.index("Antidépresseurs")
        < html.index("AINS &lt;test&gt;")
    )
    assert (
        'class="ecart-barre ecart-plus" style="--ecart: 100.0%"' in html
    )  # the largest gap fills its half
    assert 'class="ecart-barre ecart-moins" style="--ecart: 5.0%"' in html  # 2 / 40
    # bars are decoration: the text of each row carries the value
    assert html.count('class="ecart-piste" aria-hidden="true"') == 4
    assert "+40&nbsp;%" in html and "&minus;2&nbsp;%" in html
    assert "2025" in html


def test_the_table_gives_every_number_and_links_to_the_sheets():
    html = mo.tableau(LIGNES, 2025)
    assert "<caption>" in html and 'scope="col"' in html
    assert (
        '<a href="../medicaments/classes/opioides.html">Antalgiques opioïdes</a>'
        in html
    )
    assert "1&nbsp;248,6" in html and "889,3" in html and "1&nbsp;274,1" in html
    assert "AINS &lt;test&gt;" in html


def test_the_summary_names_the_largest_gaps_above_france():
    texte = mo.resume(LIGNES)
    assert "antalgiques opioïdes (+40&nbsp;%)" in texte
    assert "antidépresseurs (+27&nbsp;%)" in texte
    assert "AINS" not in texte
