"""Tests for tools/build/search_postprocess.py (accent-free copy and synonyms in the search index)."""

import search_postprocess as sp


def test_accents_are_removed():
    assert (
        sp.fold("Paracétamol, pseudoéphédrine, déglutition")
        == "paracetamol, pseudoephedrine, deglutition"
    )


def test_entry_gets_accent_free_copy_and_synonyms():
    entry = {"title": "Rhume", "text": "La pseudoéphédrine est un vasoconstricteur."}
    out = sp.enrich(entry)
    assert "pseudoephedrine" in out["text"]
    assert "decongestionnant" in out["text"]
    assert out["text"].startswith("La pseudoéphédrine")  # the original text stays first


def test_entry_without_trigger_gets_no_synonym():
    out = sp.enrich({"title": "Accès", "text": "Téléphone du centre."})
    assert "decongestionnant" not in out["text"]


def test_enrich_is_idempotent():
    entry = {"title": "Vigiking", "text": "Recevoir Vigiking."}
    once = sp.enrich(entry)
    assert sp.enrich(once) == once
