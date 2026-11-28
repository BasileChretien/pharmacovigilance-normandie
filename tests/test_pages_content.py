"""Medical facts that some pages must keep, found by the reviews of the content pull requests.
Each test names the source the page must not contradict."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def box(page: str, name: str) -> str:
    """Text of the first ::: {.name} block of a page."""
    text = (ROOT / page).read_text(encoding="utf-8")
    match = re.search(r"^::: \{\." + re.escape(name) + r"\}\n(.*?)\n:::$", text, re.S | re.M)
    assert match, f"{page}: no {name} block"
    return match.group(1)


def page(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def line_with(text: str, marker: str) -> str:
    return next(line for line in text.splitlines() if marker in line)


def test_aspirin_above_100_mg_is_contraindicated_from_the_6th_month():
    # RCP KARDEGIC 75 mg, rubrique 4.3 : « Grossesse, à partir du début du 6ème mois (au-delà
    # de 24 semaines d'aménorrhée) pour des doses d'aspirine supérieures à 100 mg par jour ».
    # The 3rd trimester (4.6) would leave 24 to 28 weeks out.
    bullet = line_with(page("medicaments/situations/grossesse-allaitement.qmd"),
                       "**Aspirine à faible dose**")
    above_100_mg = bullet.split("doses supérieures", 1)[1]
    assert "6e mois" in above_100_mg and "24 semaines" in above_100_mg
    assert "trimestre" not in above_100_mg


def test_bedtime_levothyroxine_is_not_presented_as_worse():
    # Two randomised crossover trials disagree on bedtime intake: Bach-Huynh 2009 (TSH higher
    # at bedtime than fasting) and Bolk 2010 (bedtime improved TSH and FT4 vs morning).
    text = page("bon-usage/quand-prendre.qmd")
    patient_row = line_with(text, "| Lévothyroxine (Levothyrox")
    assert "coucher" not in patient_row
    pro = text[text.index("## Pour les professionnels"):]
    assert "Bach-Huynh" in pro and "Bolk" in pro and "divergent" in pro


def test_four_cystitis_episodes_in_a_year_already_send_to_a_doctor():
    # Antibio'Malin sends to the doctor rather than the pharmacist at « 4 cystites en moins
    # d'un an », and the HAS calls a cystitis recurrent from 4 episodes in 12 months: a woman
    # with exactly 4 episodes must not read that the pharmacist will do (review of #38).
    consulter = box("medicaments/maux-courants/cystite.qmd", "quand-consulter")
    assert "4 cystites ou plus en un an" in consulter
    assert "Plus de 4 cystites" not in consulter


def test_the_levothyroxine_sheet_gives_both_bedtime_trials():
    # Same two trials as on quand-prendre: Bach-Huynh 2009 (fasting better than breakfast or
    # bedtime) and Bolk 2010 (bedtime better than morning). The sheet keeps the SmPC's morning
    # dose for patients and states the disagreement, in one bullet, for professionals.
    text = page("medicaments/classes/levothyroxine.qmd")
    patients = text[text.index("## Pour les patients"):text.index("## Pour les professionnels")]
    evening = re.search(r"\b(coucher|soir|nuit)|dormir", patients.lower())
    assert not evening, f"patient text mentions an evening dose: {evening.group(0) if evening else ''}"
    trials = line_with(text[text.index("## Pour les professionnels"):], "Bolk")
    assert "Bach-Huynh" in trials and "divergent" in trials
