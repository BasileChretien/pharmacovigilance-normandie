"""Publisher labels of further-reading links: a site is credited to the body that runs it."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _links(page: str) -> list[dict]:
    """Further-reading links of a page; the front matter ends at the first line that is only ---."""
    text = (ROOT / page).read_text(encoding="utf-8")
    front = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)[1]
    meta = yaml.safe_load(front) or {}
    return meta.get("pour_aller_plus_loin") or []


def test_who_umc_is_credited_to_the_uppsala_monitoring_centre_not_to_the_who():
    # UMC is an independent foundation, the WHO Collaborating Centre for International
    # Drug Monitoring; the WHO does not publish who-umc.org, and UMC is not "the WHO programme".
    umc = [link for link in _links("comprendre/pourquoi-declarer.qmd") if "who-umc.org" in link["url"]]
    assert umc, "the who-umc.org link is expected on this page"
    for link in umc:
        assert "Uppsala Monitoring Centre" in link["site"]
        assert "programme de pharmacovigilance de l'OMS" not in link["titre"]
