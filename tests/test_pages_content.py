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


def test_the_mac_isaac_age_bands_score_every_adult():
    # SPILF 2011: « 15 à 44 ans = 0 ; ≥ 45 ans = -1 ». The HAS sheet writes « > 45 ans »,
    # which scores no one aged exactly 45 (review of #38).
    text = page("medicaments/maux-courants/angine-mal-de-gorge.qmd")
    assert "15-44 ans : 0 ; ≥ 45 ans : −1" in text
    assert "; > 45 ans : −1" not in text


def test_the_two_migraine_boxes_give_one_eight_day_rule():
    # SFEMC 2021: acute treatment « limited to a maximum of eight days per month » (Rt4), and a
    # preventive treatment for « eight days or more per month since at least three months »
    # (Rt16a). « visez 8 jours au plus » next to « 8 jours par mois ou plus : parlez-en » sent
    # a patient at exactly 8 days both ways (review of #38).
    migraine = "medicaments/maux-courants/migraine.qmd"
    assert "ne dépassez pas 8 jours de traitement par mois" in box(migraine, "a-retenir")
    consulter = box(migraine, "quand-consulter")
    assert "8 jours de traitement par mois depuis 3 mois" in consulter
    assert "8 jours par mois ou plus" not in consulter


def test_the_2013_codeine_measures_keep_their_source():
    # rhume-toux says the contraindication after tonsillectomy « vient des mesures de 2013 sur
    # la codéine antalgique »: the HAS page that recalls them must stay in the sources
    # (review of #38).
    text = page("medicaments/maux-courants/rhume-toux.qmd")
    assert "mesures de 2013" in text
    front_matter = text.split("\n---", 1)[0]
    assert "has-sante.fr/jcms/c_2010340" in front_matter


def test_the_bupropion_contraindication_is_not_read_as_a_third_drug():
    # Thésaurus, sympathomimétiques indirects + IMAO-A réversibles: « CI - ASDEC »,
    # contraindicated when the indirect sympathomimetic is bupropion, déconseillée otherwise;
    # in a pseudoephedrine paragraph, « (contre-indication avec le bupropion) » read like a
    # third drug (review of #38).
    text = page("medicaments/maux-courants/rhume-toux.qmd")
    assert "(contre-indication avec le bupropion)" not in text
    assert "seulement quand le sympathomimétique indirect est le bupropion" in text
