"""Publisher labels of further-reading links: a site is credited to the body that runs it."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _links(page: str) -> list[dict]:
    text = (ROOT / page).read_text(encoding="utf-8")
    meta = yaml.safe_load(text.split("---", 2)[1]) or {}
    return meta.get("pour_aller_plus_loin") or []


def test_who_umc_is_credited_to_the_uppsala_monitoring_centre_not_to_the_who():
    # UMC is an independent foundation, the WHO Collaborating Centre for International
    # Drug Monitoring; the WHO does not publish who-umc.org.
    umc = [link for link in _links("comprendre/pourquoi-declarer.qmd") if "who-umc.org" in link["url"]]
    assert umc, "the who-umc.org link is expected on this page"
    for link in umc:
        assert "Uppsala Monitoring Centre" in link["site"]
        assert not link["site"].startswith("Organisation mondiale de la santé")
