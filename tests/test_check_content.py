"""Tests for tools/checks/check_content.py (writing and structure rules)."""

from pathlib import Path

import check_content as cc

FRONT = """---
title: "Test"
description: "Une page de test."
public: [patients, professionnels]
statut: {statut}
relu_par: {relu_par}
relu_le: {relu_le}
prochaine_relecture: null
sources:
  - titre: "ANSM"
    url: "https://ansm.sante.fr"
    consulte_le: 2026-11-25
---
"""

GOOD_PATIENT = """
::: {.texte-patient}

::: {.a-retenir}
- Prenez votre comprimé le matin.
- Parlez-en à votre pharmacien.
:::

### Comment le prendre ?

Prenez un comprimé chaque matin avec un verre d'eau.

::: {.quand-consulter}
- Vous saignez du nez sans arrêt.
:::

Ne modifiez pas votre traitement sans en parler à votre médecin ou à votre pharmacien.

:::
"""


def page(body, statut="brouillon", relu_par="null", relu_le="null"):
    return FRONT.format(statut=statut, relu_par=relu_par, relu_le=relu_le) + body


def rules(findings):
    return {f.rule for f in findings}


def check(text, path="medicaments/classes/test.qmd", jargon=None):
    return cc.check_text(text, Path(path), jargon=jargon or {})


# --- parsing ---------------------------------------------------------------

def test_front_matter_is_parsed():
    meta, body = cc.parse_front_matter(page(GOOD_PATIENT))
    assert meta["title"] == "Test"
    assert "texte-patient" in body


def test_fenced_div_extraction_handles_nesting():
    blocks = cc.extract_divs(GOOD_PATIENT, "texte-patient")
    assert len(blocks) == 1
    assert "a-retenir" in blocks[0]
    assert "Ne modifiez pas" in blocks[0]


def test_sentences_ignore_headings_and_comments():
    text = "### Titre\n\n<!-- FIGURE À FAIRE : schéma -->\nUne phrase. Une autre phrase !"
    assert cc.split_sentences(text) == ["Une phrase.", "Une autre phrase !"]


def test_code_blocks_are_not_sentences():
    text = "Une phrase.\n\n```{=html}\n<div class=\"outil\">un très long bloc de code html</div>\n```\n\nUne autre."
    assert cc.split_sentences(text) == ["Une phrase.", "Une autre."]


def test_list_items_are_sentences():
    assert cc.split_sentences("- premier point\n- second point") == ["premier point", "second point"]


def test_a_figure_is_read_as_its_alternative_text_and_caption():
    text = 'Avant.\n\n{{< figure-svg notice-1 alt="Une notice dépliée" legende="Les six rubriques de la notice." >}}\n\nAprès.'
    assert cc.split_sentences(text) == ["Avant.", "Une notice dépliée", "Les six rubriques de la notice.", "Après."]


def test_other_shortcodes_are_not_prose():
    text = "Avant.\n\n{{< include _includes/signal.md >}}\n\nAprès."
    assert cc.split_sentences(text) == ["Avant.", "Après."]


# --- rules -----------------------------------------------------------------

def test_good_page_has_no_errors():
    findings = check(page(GOOD_PATIENT, statut="relu", relu_par="Dr X", relu_le="2026-11-25"))
    assert [f for f in findings if f.level == "error"] == []


def test_missing_sources_is_an_error():
    text = page(GOOD_PATIENT).replace("sources:", "autres:")
    assert "FM-SOURCES" in rules(check(text))


PLUS_LOIN = """pour_aller_plus_loin:
  - titre: "Quinolones"
    url: "{url}"
    site: cnpm
"""


def test_further_reading_with_title_and_https_url_passes():
    text = page(GOOD_PATIENT).replace("sources:", PLUS_LOIN.format(url="https://pharmacomedicale.org/q") + "sources:")
    assert "FM-LIENS" not in rules(check(text))


def test_further_reading_without_url_or_with_plain_http_is_an_error():
    no_url = page(GOOD_PATIENT).replace("sources:", PLUS_LOIN.format(url="") + "sources:")
    http = page(GOOD_PATIENT).replace("sources:", PLUS_LOIN.format(url="http://example.org") + "sources:")
    assert "FM-LIENS" in rules(check(no_url))
    assert "FM-LIENS" in rules(check(http))


def test_further_reading_is_checked_on_navigation_pages_too():
    # crpv/index.qmd and vigiking/index.qmd have no statut: the link rule must still run.
    text = page(GOOD_PATIENT).replace("statut: brouillon\n", "")
    text = text.replace("sources:", PLUS_LOIN.format(url="http://www.rfcrpv.fr/missions/") + "sources:")
    assert "statut:" not in text
    assert "FM-LIENS" in rules(check(text, path="crpv/index.qmd"))


def test_institutional_page_needs_no_source():
    text = page(GOOD_PATIENT).replace("sources:", "type: institutionnel\nautres:")
    assert "FM-SOURCES" not in rules(check(text, path="a-propos/mentions-legales.qmd"))


def test_last_update_must_be_a_date():
    bad = page(GOOD_PATIENT).replace("prochaine_relecture: null", "prochaine_relecture: null\nmise_a_jour: hier")
    good = page(GOOD_PATIENT).replace("prochaine_relecture: null", "prochaine_relecture: null\nmise_a_jour: 2026-11-25")
    assert "FM-DATE" in rules(check(bad))
    assert "FM-DATE" not in rules(check(good))


def test_reviewed_page_needs_reviewer_and_date():
    findings = check(page(GOOD_PATIENT, statut="relu"))
    assert "FM-RELECTURE" in rules(findings)


def test_long_patient_sentence_is_flagged():
    long = " ".join(["mot"] * 30) + "."
    body = GOOD_PATIENT.replace("Prenez un comprimé chaque matin avec un verre d'eau.", long)
    assert "PAT-PHRASE-LONGUE" in rules(check(page(body)))


def test_percentage_in_patient_text_is_flagged():
    body = GOOD_PATIENT.replace("avec un verre d'eau", "chez 10 % des patients")
    assert "PAT-POURCENTAGE" in rules(check(page(body)))


def test_missing_a_retenir_is_flagged():
    body = GOOD_PATIENT.replace("{.a-retenir}", "{.autre}")
    assert "PAT-A-RETENIR" in rules(check(page(body)))


def test_a_retenir_with_four_points_is_flagged():
    body = GOOD_PATIENT.replace("- Parlez-en à votre pharmacien.", "- Deux.\n- Trois.\n- Quatre.")
    assert "PAT-A-RETENIR" in rules(check(page(body)))


def test_quand_consulter_required_on_drug_pages_only():
    body = GOOD_PATIENT.replace("{.quand-consulter}", "{.autre}")
    assert "PAT-QUAND-CONSULTER" in rules(check(page(body)))
    assert "PAT-QUAND-CONSULTER" not in rules(check(page(body), path="comprendre/test.qmd"))


def test_unexplained_jargon_is_flagged_and_explained_jargon_is_not():
    jargon = {"hémorragie": "saignement"}
    bad = GOOD_PATIENT.replace("avec un verre d'eau", "contre une hémorragie")
    good = GOOD_PATIENT.replace("avec un verre d'eau", "contre une hémorragie (saignement)")
    assert "PAT-JARGON" in rules(check(page(bad), jargon=jargon))
    assert "PAT-JARGON" not in rules(check(page(good), jargon=jargon))


def test_unexpanded_acronym_is_flagged():
    bad = GOOD_PATIENT.replace("avec un verre d'eau", "selon l'ANSM")
    good = GOOD_PATIENT.replace("avec un verre d'eau", "selon l'Agence du médicament (ANSM)")
    assert "PAT-SIGLE" in rules(check(page(bad)))
    assert "PAT-SIGLE" not in rules(check(page(good)))


def test_missing_do_not_stop_sentence_is_flagged():
    body = GOOD_PATIENT.replace("Ne modifiez pas votre traitement", "Continuez")
    assert "PAT-NE-PAS-ARRETER" in rules(check(page(body)))


def test_draft_findings_are_warnings_but_published_are_errors():
    long = " ".join(["mot"] * 30) + "."
    body = GOOD_PATIENT.replace("Prenez un comprimé chaque matin avec un verre d'eau.", long)
    draft = [f for f in check(page(body)) if f.rule == "PAT-PHRASE-LONGUE"]
    published = [
        f for f in check(page(body, statut="publie", relu_par="Dr X", relu_le="2026-11-25"))
        if f.rule == "PAT-PHRASE-LONGUE"
    ]
    assert draft[0].level == "warning"
    assert published[0].level == "error"


def test_command_line_fails_on_error_and_passes_on_clean_page(tmp_path, capsys):
    bad = tmp_path / "sans-source.qmd"
    bad.write_text(page(GOOD_PATIENT).replace("sources:", "autres:"), encoding="utf-8")
    good = tmp_path / "propre.qmd"
    good.write_text(page(GOOD_PATIENT), encoding="utf-8")
    assert cc.main([str(bad)]) == 1
    assert cc.main([str(good)]) == 0
    assert "FM-SOURCES" in capsys.readouterr().out


def test_readability_score_is_reported():
    score = cc.kandel_moles("Prenez un comprimé le matin. Buvez un verre d'eau.")
    assert 0 < score <= 130


# --- official notice and SmPC links (data/bdpm-liens.json) ---------------------

BDPM = {
    "mis_a_jour": "2026-11-20",
    "substances": {"ibuprofène": {"cis": "68634000", "nom": "ADVIL 200 mg, comprimé enrobé"}},
    "cites": {
        "68634000": {"nom": "ADVIL 200 mg, comprimé enrobé", "etat": "Commercialisée"},
        "60000006": {"nom": "ANCIEN 10 mg, comprimé", "etat": "Non commercialisée"},
    },
}


def _bdpm_page(cis, substances="[ibuprofène]"):
    return (
        "---\ntitle: T\ndescription: D\nstatut: brouillon\n"
        f"substances: {substances}\nsources:\n"
        '  - titre: "BDPM"\n'
        f'    url: "https://base-donnees-publique.medicaments.gouv.fr/medicament/{cis}/extrait"\n'
        "---\n\nTexte.\n"
    )


def _bdpm_findings(text):
    return [f for f in cc.check_text(text, Path("medicaments/classes/x.qmd"), {}, bdpm=BDPM) if f.rule == "FM-BDPM"]


def test_a_cited_product_still_marketed_passes():
    assert _bdpm_findings(_bdpm_page("68634000")) == []


def test_a_cited_product_no_longer_marketed_is_an_error():
    findings = _bdpm_findings(_bdpm_page("60000006"))
    assert [f.level for f in findings] == ["error"]
    assert "Non commercialisée" in findings[0].message


def test_a_cited_product_not_yet_checked_is_a_warning():
    findings = _bdpm_findings(_bdpm_page("61111111"))
    assert [f.level for f in findings] == ["warning"]
    assert "make_bdpm_liens.py" in findings[0].message


def test_a_substance_without_an_official_link_is_a_warning():
    findings = _bdpm_findings(_bdpm_page("68634000", substances="[ibuprofène, inconnue]"))
    assert [f.level for f in findings] == ["warning"]
    assert "inconnue" in findings[0].message


def test_without_bdpm_data_the_rule_is_skipped():
    findings = cc.check_text(_bdpm_page("60000006"), Path("medicaments/classes/x.qmd"), {})
    assert not [f for f in findings if f.rule == "FM-BDPM"]
