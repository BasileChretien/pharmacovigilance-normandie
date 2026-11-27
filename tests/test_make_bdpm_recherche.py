"""Tests for tools/build/make_bdpm_recherche.py (index of the drug-name search page)."""

import make_bdpm_liens as mb
import make_bdpm_recherche as mr


def _row(
    cis,
    nom,
    voies="orale",
    procedure="Procédure nationale",
    etat="Commercialisée",
    statut="Autorisation active",
):
    # The 12 columns of CIS_bdpm.txt.
    colonnes = [
        cis,
        nom,
        "comprimé",
        voies,
        statut,
        procedure,
        etat,
        "01/01/2000",
        "",
        "",
        " LAB",
        "Non",
    ]
    return "\t".join(colonnes)


SPECIALITES = "\n".join(
    [
        _row("68634000", "ADVIL 200 mg, comprimé enrobé"),
        _row("60000004", "PARACETAMOL CODEINE ARROW 500 mg/30 mg, comprimé"),
        _row(
            "60000006",
            "ANCIEN 10 mg, comprimé",
            etat="Non commercialisée",
            statut="Autorisation abrogée",
        ),
        _row(
            "69103878",
            "ARNICA MONTANA BOIRON, granules",
            procedure="Enreg homéo (Proc. Nat.)",
        ),
        _row(
            "60000012",
            "XARELTO 10 mg, comprimé pelliculé",
            procedure="Procédure centralisée",
        ),
        # Homeopathic medicines with a full marketing authorisation, not a registration.
        _row("60000014", "OSCILLO TEST, granules en récipient unidose"),
        _row("60000015", "SOUCHE TEST 9 CH, granules"),
    ]
)
COMPOSITIONS = "\n".join(
    "\t".join(r)
    for r in [
        [
            "60000014",
            "granules",
            "09",
            "EXTRAIT FLUIDE PEPTONÉ DE FOIE ET DE COEUR D'ANAS BARBARIAE DYNAMISÉ À LA 200E K",
            "1 g",
            "un récipient",
            "SA",
            "1",
        ],
        [
            "60000015",
            "granules",
            "10",
            "ARNICA MONTANA POUR PRÉPARATIONS HOMÉOPATHIQUES",
            "9CH",
            "un granule",
            "SA",
            "1",
        ],
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
            "69103878",
            "granules",
            "07",
            "ARNICA MONTANA POUR PRÉPARATIONS HOMÉOPATHIQUES",
            "4CH",
            "un granule",
            "SA",
            "1",
        ],
        [
            "60000012",
            "comprimé",
            "08",
            "RIVAROXABAN",
            "10 mg",
            "un comprimé",
            "SA",
            "1",
        ],
    ]
)
FICHES = {
    "medicaments/classes/ains.qmd": (
        "Les anti-inflammatoires non stéroïdiens (AINS)",
        ["ibuprofène", "kétoprofène"],
    ),
    "medicaments/classes/opioides.qmd": ("Les médicaments opioïdes", ["codéine"]),
}


def _index():
    base = mb.Base.from_texts(SPECIALITES, COMPOSITIONS, "")
    return mr.index(base, FICHES, "2026-11-20")


def test_only_marketed_medicines_are_listed_and_homeopathy_is_left_out():
    noms = [m[1] for m in _index()["medicaments"]]
    assert noms == [
        "ADVIL 200 mg, comprimé enrobé",
        "PARACETAMOL CODEINE ARROW 500 mg/30 mg, comprimé",
        "XARELTO 10 mg, comprimé pelliculé",
    ]  # sorted by name; not the withdrawn one, not the homeopathic one


def test_each_medicine_names_its_substances_the_active_part_first():
    data = _index()
    by_name = {m[1]: [data["substances"][i] for i in m[2]] for m in data["medicaments"]}
    assert by_name["PARACETAMOL CODEINE ARROW 500 mg/30 mg, comprimé"] == [
        "paracétamol",
        "codéine",
    ]
    assert by_name["XARELTO 10 mg, comprimé pelliculé"] == ["rivaroxaban"]


def test_a_substance_with_a_sheet_on_the_site_points_to_it():
    data = _index()
    fiches = {data["substances"][int(i)]: f for i, f in data["fiches"].items()}
    assert fiches["ibuprofène"] == [
        [
            "medicaments/classes/ains.html",
            "Les anti-inflammatoires non stéroïdiens (AINS)",
        ]
    ]
    assert fiches["codéine"] == [
        ["medicaments/classes/opioides.html", "Les médicaments opioïdes"]
    ]
    assert "rivaroxaban" not in fiches


def test_the_index_carries_its_source_and_date():
    data = _index()
    assert data["mis_a_jour"] == "2026-11-20"
    assert data["source"].startswith(
        "https://base-donnees-publique.medicaments.gouv.fr"
    )
    assert all(m[0].isdigit() and len(m[0]) == 8 for m in data["medicaments"])


def test_sheets_are_read_with_their_title_and_substances(tmp_path):
    (tmp_path / "medicaments" / "classes").mkdir(parents=True)
    (tmp_path / "medicaments" / "classes" / "ains.qmd").write_text(
        '---\ntitle: "Les AINS"\nsubstances: [ibuprofène]\n---\n\nTexte.\n',
        encoding="utf-8",
    )
    (tmp_path / "autre.qmd").write_text("---\ntitle: Autre\n---\n", encoding="utf-8")
    assert mr.lire_fiches(tmp_path) == {
        "medicaments/classes/ains.qmd": ("Les AINS", ["ibuprofène"])
    }


def test_the_page_states_the_files_date_and_the_count():
    html = mr.source_html(
        {
            "source": mb.SOURCE,
            "mis_a_jour": "2026-11-20",
            "medicaments": [["1", "X", []]] * 12312,
        }
    )
    assert "fichiers du 20/11/2026" in html
    assert "12&nbsp;312 médicaments" in html
    assert f'href="{mb.SOURCE}"' in html


def test_an_inverted_salt_and_every_sheet_of_a_substance_are_linked():
    specialites = "\n".join(
        [
            _row("60000020", "DEPAKINE 200 mg, comprimé gastro-résistant"),
            _row("60000021", "CODOLIPRANE, comprimé"),
        ]
    )
    lignes = [
        [
            "60000020",
            "comprimé",
            "20",
            "SODIUM (VALPROATE DE)",
            "200 mg",
            "un comprimé",
            "SA",
            "1",
        ],
        ["60000021", "comprimé", "21", "CODÉINE", "20 mg", "un comprimé", "SA", "1"],
    ]
    compositions = "\n".join("\t".join(colonnes) for colonnes in lignes)
    fiches = {
        "medicaments/classes/valproate-teratogenes.qmd": (
            "Le valproate",
            ["valproate de sodium"],
        ),
        "medicaments/classes/opioides.qmd": ("Les opioïdes", ["codéine"]),
        "medicaments/maux-courants/toux.qmd": ("La toux", ["codéine"]),
    }
    data = mr.index(
        mb.Base.from_texts(specialites, compositions, ""), fiches, "2026-11-20"
    )
    liens = {data["substances"][int(i)]: f for i, f in data["fiches"].items()}
    assert liens["sodium (valproate de)"] == [
        ["medicaments/classes/valproate-teratogenes.html", "Le valproate"]
    ]
    assert liens["codéine"] == [
        ["medicaments/classes/opioides.html", "Les opioïdes"],
        ["medicaments/maux-courants/toux.html", "La toux"],
    ]
