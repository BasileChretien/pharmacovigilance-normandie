"""Medical facts that some pages must keep, found by the merge-gate reviews of the content
audits. Each test names the source sentence the page must not contradict."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    assert "6e mois" in bullet and "24 semaines" in bullet
    assert "troisième trimestre" not in bullet


def test_bedtime_levothyroxine_is_not_presented_as_worse():
    # Two randomised crossover trials disagree on bedtime intake: Bach-Huynh 2009 (TSH higher
    # at bedtime than fasting) and Bolk 2010 (bedtime improved TSH and FT4 vs morning).
    text = page("bon-usage/quand-prendre.qmd")
    patient_row = line_with(text, "| Lévothyroxine (Levothyrox")
    assert "coucher" not in patient_row
    pro = text[text.index("## Pour les professionnels"):]
    assert "Bach-Huynh" in pro and "Bolk" in pro
