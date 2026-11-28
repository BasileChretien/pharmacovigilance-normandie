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


def test_four_cystitis_episodes_in_a_year_already_send_to_a_doctor():
    # Antibio'Malin sends to the doctor rather than the pharmacist at « 4 cystites en moins
    # d'un an », and the HAS calls a cystitis recurrent from 4 episodes in 12 months: a woman
    # with exactly 4 episodes must not read that the pharmacist will do (review of #38).
    consulter = box("medicaments/maux-courants/cystite.qmd", "quand-consulter")
    assert "4 cystites ou plus en un an" in consulter
    assert "Plus de 4 cystites" not in consulter
