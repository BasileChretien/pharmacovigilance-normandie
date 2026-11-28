"""Tests for tools/build/fetch_publications.py and make_publications_page.py (the teams'
recent publications on crpv/recherche.qmd)."""

import datetime as dt
import json
import urllib.error

import fetch_publications as fp
import make_publications_page as mp
import pytest

# ORCID's fictional test researcher (Josiah Carberry) and a made-up iD with a valid check
# digit: no real person's.
CARBERRY = "0000-0002-1825-0097"
AUTRE = "0000-0009-9999-9980"
AUJOURD_HUI = dt.date(2026, 11, 28)


def _equipes(tmp_path, caen: str, rouen: str = ""):
    (tmp_path / "crpv").mkdir()
    (tmp_path / "crpv" / "equipe-caen.qmd").write_text(caen, encoding="utf-8")
    (tmp_path / "crpv" / "equipe-rouen.qmd").write_text(rouen, encoding="utf-8")
    return tmp_path


def _orcid(*groupes):
    """An ORCID /works answer: one group per (doi, year)."""
    return {
        "group": [
            {
                "external-ids": {
                    "external-id": [
                        {
                            "external-id-type": "issn",
                            "external-id-value": "0264-3561",
                            "external-id-relationship": "part-of",
                        },
                        {
                            "external-id-type": "doi",
                            "external-id-value": doi,
                            "external-id-relationship": "self",
                        },
                    ]
                },
                "work-summary": [
                    {"publication-date": {"year": {"value": annee}} if annee else None}
                ],
            }
            for doi, annee in groupes
        ]
    }


def _oeuvre(doi, titre="Titre", date="2025-03-01", type_="article", **plus):
    return {
        "doi": f"https://doi.org/{doi}",
        "display_name": titre,
        "publication_date": date,
        "type": type_,
        "language": "en",
        "primary_location": {"source": {"display_name": "Drug Safety"}},
        "open_access": {"is_oa": False, "oa_url": None},
        "is_retracted": False,
        **plus,
    }


def test_member_cards_give_the_orcid_ids_and_their_team(tmp_path):
    racine = _equipes(
        tmp_path,
        f"[ORCID](https://orcid.org/{CARBERRY}) [ORCID](https://orcid.org)\n"
        f"<!-- carte retirée : [ORCID](https://orcid.org/{AUTRE}) -->",
        f"[ORCID](https://orcid.org/{CARBERRY})",
    )
    assert fp.membres(racine) == ({CARBERRY: ["caen", "rouen"]}, [])


def test_an_orcid_link_that_gives_no_valid_id_is_reported_not_ignored(tmp_path):
    racine = _equipes(
        tmp_path,
        "[ORCID](https://orcid.org/0000-0002-1825-0098) "  # wrong check digit
        "[ORCID](https://orcid.org/0000-0002-1825-00977) "  # one digit too many
        "[ORCID](https://orcid.org/0000-0009-9999-993x) "  # lower-case x: fine
        f"[ORCID](https://orcid.org/{CARBERRY}/)",  # trailing slash: fine
    )
    valides, illisibles = fp.membres(racine)
    assert valides == {"0000-0009-9999-993X": ["caen"], CARBERRY: ["caen"]}
    assert illisibles == [
        ("crpv/equipe-caen.qmd", "0000-0002-1825-0098"),
        ("crpv/equipe-caen.qmd", "0000-0002-1825-00977"),
    ]


def test_the_check_digit_can_be_x():
    assert fp.orcid_valide("0000-0009-9999-993X")
    assert not fp.orcid_valide("0000-0009-9999-9930")


def test_dois_are_normalised_and_unusable_ones_dropped():
    assert (
        fp.normaliser_doi(" https://doi.org/10.1007/S40264-020-00950-3 ")
        == "10.1007/s40264-020-00950-3"
    )
    for ecrit in (
        "doi:10.1002/pds.5000",
        "doi: 10.1002/pds.5000",
        "http://dx.doi.org/10.1002/PDS.5000",
        "doi.org/10.1002/pds.5000",
        "https://doi.org/10.1002%2Fpds.5000",
    ):
        assert fp.normaliser_doi(ecrit) == "10.1002/pds.5000", ecrit
    assert fp.normaliser_doi("10.1000/a,b") is None
    assert fp.normaliser_doi("pas un doi") is None


def test_orcid_works_before_the_window_are_left_out_but_undated_ones_kept():
    reponse = _orcid(
        ("10.1000/a", "2026"),
        ("10.1000/b", "2019"),
        ("10.1000/c", None),
        ("10.1000/a", "2026"),
    )
    assert fp.dois_orcid(reponse, 2024) == ["10.1000/a", "10.1000/c"]


def test_an_orcid_group_gives_its_first_usable_doi_and_its_latest_year():
    groupe = {
        "external-ids": {
            "external-id": [
                {
                    "external-id-type": "doi",
                    "external-id-value": "pas un doi",
                    "external-id-relationship": "self",
                },
                {
                    "external-id-type": "doi",
                    "external-id-value": "https://doi.org/10.1000/BRUT",
                    "external-id-normalized": {"value": "10.1000/brut"},
                    "external-id-relationship": "self",
                },
            ]
        },
        # Two versions of the work: the older one first.
        "work-summary": [
            {"publication-date": {"year": {"value": "2019"}}},
            {"publication-date": {"year": {"value": "2025"}}},
        ],
    }
    assert fp.dois_orcid({"group": [groupe]}, 2024) == ["10.1000/brut"]


def test_no_member_card_means_no_request_and_an_empty_list():
    def ne_pas_appeler(url):
        raise AssertionError(url)

    data = fp.releve({}, ne_pas_appeler, AUJOURD_HUI)
    assert data == {
        "releve_le": "2026-11-28",
        "depuis": 2024,
        "membres": [],
        "non_lus": [],
        "publications": [],
    }


def test_orcid_then_openalex_give_one_entry_per_work_newest_first():
    reponses = {
        fp.ORCID_API.format(CARBERRY): _orcid(
            ("10.1000/a", "2025"), ("10.1000/b", "2026"), ("10.1000/p", "2026")
        ),
        fp.ORCID_API.format(AUTRE): _orcid(("10.1000/a", "2025")),
    }
    vus = []

    def fetch(url):
        vus.append(url)
        if url in reponses:
            return reponses[url]
        assert "from_publication_date%3A2024-01-01" in url
        return {
            "results": [
                _oeuvre("10.1000/a", "<i>Older</i> &amp; shared", "2025-03-01"),
                _oeuvre(
                    "10.1000/b",
                    "Newer",
                    "2026-06-02",
                    open_access={"is_oa": True, "oa_url": "https://pmc.example/1"},
                    is_retracted=True,
                ),
                _oeuvre("10.1000/p", "A preprint", "2026-01-01", type_="preprint"),
                _oeuvre("10.1000/z", "Not listed by a member"),
            ]
        }

    data = fp.releve({CARBERRY: ["caen"], AUTRE: ["rouen"]}, fetch, AUJOURD_HUI)
    assert len(vus) == 3
    titres = [p["titre"] for p in data["publications"]]
    assert titres == ["Newer", "Older & shared"]
    newer, older = data["publications"]
    assert newer["acces_libre"] == "https://pmc.example/1" and newer["retracte"] is True
    assert older["equipes"] == ["caen", "rouen"] and older["membres"] == sorted(
        [CARBERRY, AUTRE]
    )
    assert older["revue"] == "Drug Safety" and older["langue"] == "en"


def _panne_pour(orcid, code):
    def fetch(url):
        if url == fp.ORCID_API.format(orcid):
            raise urllib.error.HTTPError(url, code, "x", None, None)
        if url.startswith("https://pub.orcid.org/"):
            return _orcid(("10.1000/a", "2025"))
        return {"results": [_oeuvre("10.1000/a")]}

    return fetch


def test_a_member_whose_orcid_record_is_gone_is_marked_not_read_and_others_listed():
    for code in (404, 409, 410):
        data = fp.releve(
            {CARBERRY: ["caen"], AUTRE: ["rouen"]},
            _panne_pour(AUTRE, code),
            AUJOURD_HUI,
        )
        assert data["non_lus"] == [AUTRE]
        assert [p["membres"] for p in data["publications"]] == [[CARBERRY]]


def test_an_orcid_outage_is_not_blamed_on_one_member():
    with pytest.raises(urllib.error.HTTPError):
        fp.releve({AUTRE: ["rouen"]}, _panne_pour(AUTRE, 503), AUJOURD_HUI)


def test_a_free_access_link_that_is_not_a_web_address_is_dropped():
    oeuvre = _oeuvre(
        "10.1000/a", open_access={"is_oa": True, "oa_url": "javascript:alert(1)"}
    )
    assert fp.notice(oeuvre, {CARBERRY: ["caen"]})["acces_libre"] is None


def test_a_failed_fetch_keeps_the_previous_list_without_the_works_of_departed_members(
    tmp_path,
):
    chemin = tmp_path / "publications.json"
    commun = {
        "doi": "10.1000/a",
        "titre": "A",
        "revue": None,
        "publie_le": "2025-01-01",
        "langue": None,
        "acces_libre": None,
        "retracte": False,
    }
    chemin.write_text(
        json.dumps(
            {
                "releve_le": "2026-11-23",
                "depuis": 2024,
                "membres": [AUTRE, CARBERRY],
                "publications": [
                    {
                        **commun,
                        "membres": [AUTRE, CARBERRY],
                        "equipes": ["caen", "rouen"],
                    },
                    {
                        **commun,
                        "doi": "10.1000/b",
                        "titre": "B",
                        "membres": [AUTRE],
                        "equipes": ["rouen"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    data = fp.precedent(chemin, {CARBERRY: ["caen"]})
    assert data["releve_le"] == "2026-11-23" and data["membres"] == [CARBERRY]
    assert data["non_lus"] == []
    assert [(p["doi"], p["membres"], p["equipes"]) for p in data["publications"]] == [
        ("10.1000/a", [CARBERRY], ["caen"])
    ]


def _ecrire_precedent(chemin, membres, non_lus=None):
    data = {
        "releve_le": "2026-11-23",
        "depuis": 2024,
        "membres": membres,
        "publications": [
            {
                "doi": f"10.1000/{i}",
                "titre": f"T{i}",
                "revue": None,
                "publie_le": "2025-01-01",
                "langue": None,
                "acces_libre": None,
                "retracte": False,
                "membres": [m],
                "equipes": ["caen"],
            }
            for i, m in enumerate(membres)
        ],
    }
    if non_lus is not None:
        data["non_lus"] = non_lus
    chemin.write_text(json.dumps(data), encoding="utf-8")


def test_a_member_the_previous_list_never_read_is_marked_not_read(tmp_path):
    chemin = tmp_path / "publications.json"
    _ecrire_precedent(chemin, [CARBERRY])
    data = fp.precedent(chemin, {CARBERRY: ["caen"], AUTRE: ["rouen"]})
    assert data["membres"] == sorted([CARBERRY, AUTRE]) and data["non_lus"] == [AUTRE]
    assert [p["membres"] for p in data["publications"]] == [[CARBERRY]]
    # A member the previous list could not read stays not read.
    _ecrire_precedent(chemin, [CARBERRY, AUTRE], non_lus=[AUTRE])
    assert fp.precedent(chemin, {CARBERRY: ["caen"], AUTRE: ["rouen"]})["non_lus"] == [
        AUTRE
    ]


def test_a_damaged_previous_file_counts_as_none(tmp_path):
    chemin = tmp_path / "publications.json"
    chemin.write_text(
        '{"releve_le": "2026-99-99", "depuis": 2024, "publications": []}',
        encoding="utf-8",
    )
    assert fp.precedent(chemin, {}) is None
    chemin.write_text("pas du json", encoding="utf-8")
    assert fp.precedent(chemin, {}) is None


def test_main_writes_the_not_read_state_when_the_sites_fail_and_nothing_is_kept(
    tmp_path, monkeypatch
):
    sortie = tmp_path / "data" / "publications.json"
    monkeypatch.setattr(fp, "OUT", sortie)
    monkeypatch.setattr(fp, "membres", lambda: ({CARBERRY: ["caen"]}, []))

    def panne(url):
        raise OSError("hors ligne")

    monkeypatch.setattr(fp, "_fetch", panne)
    assert fp.main() == 1
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert data == {
        "releve_le": None,
        "depuis": None,
        "membres": [CARBERRY],
        "non_lus": [CARBERRY],
        "publications": [],
    }
    assert "liste n'a pas encore pu être relevée" in mp.liste(data)


def test_the_page_waits_for_member_cards_before_listing_anything():
    assert "carte" in mp.liste({"membres": [], "publications": []})
    assert "carte" in mp.liste(None)


def test_an_empty_list_shows_the_decorative_mascot_and_a_filled_one_does_not():
    mascotte = '<img class="mascotte" src="../assets/img/mascotte.svg" alt="" aria-hidden="true"'
    lu = {"releve_le": "2026-11-28", "depuis": 2024, "membres": [CARBERRY], "non_lus": []}
    vides = [
        None,
        {"membres": [], "publications": []},
        {**lu, "releve_le": None, "non_lus": [CARBERRY], "publications": []},
        {**lu, "publications": []},
    ]
    for data in vides:
        page = mp.liste(data)
        assert mascotte in page and '<div class="etat-vide">' in page, data
    oeuvre = {
        "doi": "10.1000/a", "titre": "Titre", "revue": None, "publie_le": "2026-06-02",
        "langue": "fr", "acces_libre": None, "retracte": False, "membres": [CARBERRY],
        "equipes": ["caen"],
    }  # fmt: skip
    assert "mascotte" not in mp.liste({**lu, "publications": [oeuvre]})


def test_the_page_lists_title_year_journal_team_without_author_names():
    data = {
        "releve_le": "2026-11-28",
        "depuis": 2024,
        "membres": [CARBERRY],
        "publications": [
            {
                "doi": "10.1000/a",
                "titre": "Tegretol <script>alert(1)</script>",
                "revue": "Thérapie",
                "publie_le": "2026-06-02",
                "langue": "fr",
                "acces_libre": "https://hal.example/1?a=1&b=2",
                "retracte": True,
                "membres": [CARBERRY],
                "equipes": ["caen", "rouen"],
            },
            {
                "doi": "10.1000/b",
                "titre": "Drug safety",
                "revue": None,
                "publie_le": "2025-01-01",
                "langue": "en",
                "acces_libre": None,
                "retracte": False,
                "membres": [CARBERRY],
                "equipes": ["rouen"],
            },
        ],
    }
    page = mp.liste(data)
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert '<a href="https://doi.org/10.1000/a">' in page
    assert "<em>Thérapie</em>" in page and '<time datetime="2026">2026</time>' in page
    assert "Équipes de Caen et de Rouen" in page and "Équipe de Rouen" in page
    assert 'href="https://hal.example/1?a=1&amp;b=2"' in page and "rétracté" in page
    assert '<p class="fil-titre" lang="en">' in page
    assert page.count('lang="en"') == 1  # the French title gets no lang attribute
    assert CARBERRY not in page and "relevée le" in page


def test_free_access_at_the_doi_itself_is_not_a_second_link():
    item = mp._item(
        {
            "doi": "10.1000/a",
            "titre": "T",
            "revue": None,
            "publie_le": "2026-01-01",
            "langue": None,
            "acces_libre": "https://doi.org/10.1000/A",
            "retracte": False,
            "equipes": ["caen"],
        }
    )
    assert item.count("<a ") == 1 and "en accès libre" in item


def test_an_answer_of_an_unexpected_shape_keeps_the_previous_list(
    tmp_path, monkeypatch
):
    sortie = tmp_path / "publications.json"
    monkeypatch.setattr(fp, "OUT", sortie)
    monkeypatch.setattr(fp, "membres", lambda: ({CARBERRY: ["caen"]}, []))
    monkeypatch.setattr(fp, "_fetch", lambda url: {"group": ["pas un groupe"]})
    assert fp.main() == 1
    assert json.loads(sortie.read_text(encoding="utf-8"))["releve_le"] is None


def test_a_new_member_after_the_committed_seed_is_not_read_yet_not_without_works(
    tmp_path, monkeypatch
):
    # The committed seed: read on a date, but before any card gave an iD.
    sortie = tmp_path / "publications.json"
    sortie.write_text(
        json.dumps(
            {
                "releve_le": "2026-11-28",
                "depuis": 2024,
                "membres": [],
                "publications": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(fp, "OUT", sortie)
    monkeypatch.setattr(fp, "membres", lambda: ({CARBERRY: ["caen"]}, []))

    def panne(url):
        raise OSError("hors ligne")

    monkeypatch.setattr(fp, "_fetch", panne)
    assert fp.main() == 1
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert "pas encore pu être relevée" in mp.liste(data)
    assert "Aucune publication" not in mp.liste(data)


def test_an_unreadable_card_id_is_named_and_departed_works_still_go(
    tmp_path, monkeypatch, capsys
):
    # In one commit: AUTRE's card goes and another card gets a typo in its iD; the sites
    # are down. AUTRE's works must not stay, and the log names the typo.
    sortie = tmp_path / "publications.json"
    _ecrire_precedent(sortie, [CARBERRY, AUTRE])
    faute = "0000-0002-1825-0098"
    monkeypatch.setattr(fp, "OUT", sortie)
    monkeypatch.setattr(
        fp,
        "membres",
        lambda: ({CARBERRY: ["caen"]}, [("crpv/equipe-rouen.qmd", faute)]),
    )

    def panne(url):
        raise OSError("hors ligne")

    monkeypatch.setattr(fp, "_fetch", panne)
    assert fp.main() == 1
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert [p["membres"] for p in data["publications"]] == [[CARBERRY]]
    assert data["non_lus"] == [faute] and faute in data["membres"]
    erreurs = capsys.readouterr().err
    assert faute in erreurs and "crpv/equipe-rouen.qmd" in erreurs


def test_the_page_says_how_many_members_could_not_be_read():
    publication = {
        "doi": "10.1000/a",
        "titre": "T",
        "revue": None,
        "publie_le": "2026-01-01",
        "langue": None,
        "acces_libre": None,
        "retracte": False,
        "membres": [CARBERRY],
        "equipes": ["caen"],
    }
    data = {
        "releve_le": "2026-11-28",
        "depuis": 2024,
        "membres": [AUTRE, CARBERRY],
        "non_lus": [AUTRE],
        "publications": [publication],
    }
    page = mp.liste(data)
    assert "d'un membre n'ont pas pu être relevées" in page and "fil-alertes" in page
    assert AUTRE not in page
    # Every member unread: the list was not read at all.
    page = mp.liste({**data, "non_lus": [AUTRE, CARBERRY], "publications": []})
    assert "pas encore pu être relevée" in page


def test_a_doi_is_percent_encoded_in_its_link():
    item = mp._item(
        {
            "doi": "10.1000/a#b?c%d",
            "titre": "T",
            "revue": None,
            "publie_le": "2026-01-01",
            "langue": None,
            "acces_libre": None,
            "retracte": False,
            "equipes": ["caen"],
        }
    )
    assert 'href="https://doi.org/10.1000/a%23b%3Fc%25d"' in item


def test_an_orcid_answer_that_fails_for_every_member_is_an_outage(
    tmp_path, monkeypatch
):
    # ORCID retiring its API version would answer 410 for every iD: keep the list.
    sortie = tmp_path / "publications.json"
    _ecrire_precedent(sortie, [CARBERRY, AUTRE])
    monkeypatch.setattr(fp, "OUT", sortie)
    monkeypatch.setattr(
        fp, "membres", lambda: ({CARBERRY: ["caen"], AUTRE: ["rouen"]}, [])
    )

    def disparu(url):
        raise urllib.error.HTTPError(url, 410, "Gone", None, None)

    monkeypatch.setattr(fp, "_fetch", disparu)
    assert fp.main() == 1
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert len(data["publications"]) == 2 and data["releve_le"] == "2026-11-23"


def test_an_orcid_link_followed_by_punctuation_is_read(tmp_path):
    racine = _equipes(
        tmp_path,
        f"ORCID : https://orcid.org/{CARBERRY}. Ou **https://orcid.org/{CARBERRY}**, "
        f"(https://orcid.org/{CARBERRY});",
    )
    assert fp.membres(racine) == ({CARBERRY: ["caen"]}, [])


def test_a_single_member_whose_record_is_locked_is_not_read_while_orcid_answers(
    tmp_path, monkeypatch, capsys
):
    # One card, its record locked (409); ORCID's own test record still answers.
    sortie = tmp_path / "publications.json"
    _ecrire_precedent(sortie, [AUTRE])
    monkeypatch.setattr(fp, "OUT", sortie)
    monkeypatch.setattr(fp, "membres", lambda: ({AUTRE: ["rouen"]}, []))

    def fetch(url):
        if url == fp.ORCID_API.format(fp.TEMOIN):
            return _orcid(("10.1000/temoin", "2012"))
        raise urllib.error.HTTPError(url, 409, "Conflict", None, None)

    monkeypatch.setattr(fp, "_fetch", fetch)
    assert fp.main() == 1
    data = json.loads(sortie.read_text(encoding="utf-8"))
    assert data["non_lus"] == [AUTRE] and data["publications"] == []
    assert AUTRE in capsys.readouterr().err
