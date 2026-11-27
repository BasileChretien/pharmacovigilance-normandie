"""Fetch the ANSM list of regional pharmacovigilance centres (CRPV) and the departments
each one covers, for the page "Trouver votre centre" (crpv/trouver-mon-crpv.qmd).

Writes data/crpv-france.json: per centre, its name, departments (Paris by arrondissement,
split departments with their part), phone, email and website. The name of the head of
each centre is not kept (no real person's name on the site without consent).

Run by hand when the list changes: python tools/build/fetch_crpv.py
Then: python tools/build/make_crpv_page.py
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "crpv-france.json"
SOURCE = "https://ansm.sante.fr/page/liste-des-centres-regionaux-de-pharmacovigilance"

_TAG = re.compile(r"<[^>]+>")
_ITEM = re.compile(
    r'<div class="accordion-item">(.*?)(?=<div class="accordion-item">|\Z)', re.DOTALL
)
_HEADING = re.compile(r'<a class="accordion-heading"[^>]*>(.*?)</a>', re.DOTALL)
_DEPTS = re.compile(
    r"D(?:é|&eacute;)partements? concern(?:é|&eacute;)s? :\s*<ul[^>]*>(.*?)</ul>",
    re.DOTALL,
)
_LI = re.compile(r"<li>(.*?)</li>", re.DOTALL)
_DEPT = re.compile(r"^(?P<nom>.+?)\s*\((?P<code>\d{2,3}|2A|2B)\)$")
_PARIS = re.compile(r"^Paris\s+(?P<arr>\d+(?:-\d+)*)\s*\(")
_SPLIT = re.compile(r"^(?P<nom>.+?)\s+(?P<part>Nord|Sud|Est|Ouest)$")
_PHONE = re.compile(r"T(?:é|&eacute;)l(?:é|&eacute;)phone\s*:\s*([0-9][0-9 .]{8,})")
_MAIL = re.compile(r'href="mailto:([^"]+)"')
_SITE = re.compile(
    r'<a[^>]*href="(https?://[^"]+)"[^>]*>\s*Acceder au site Internet', re.DOTALL
)
_UPDATE = re.compile(r"MIS (?:À|&Agrave;) JOUR LE (\d{2})/(\d{2})/(\d{4})")


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", fragment))).strip()


def parse_update_date(page: str) -> str | None:
    """ISO date of the list's last update, as the ANSM page states it."""
    m = _UPDATE.search(page)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def parse_departement(label: str) -> dict:
    """'Calvados (14)' -> code, name; 'Yvelines Nord (78)' keeps its part; Paris keeps
    its arrondissements, read from the numbers before the brackets (the codes in the
    brackets are mistyped on the ANSM page, e.g. 750014)."""
    label = _text(label)
    paris = _PARIS.match(label)
    if paris:
        arrondissements = [int(n) for n in paris.group("arr").split("-")]
        return {
            "code": "75",
            "nom": "Paris",
            "precision": None,
            "arrondissements": arrondissements,
        }
    m = _DEPT.match(label)
    if not m:
        raise ValueError(f"département illisible : {label!r}")
    nom, precision = m.group("nom"), None
    split = _SPLIT.match(nom)
    if split:
        nom, precision = split.group("nom"), split.group("part")
    return {
        "code": m.group("code"),
        "nom": nom,
        "precision": precision,
        "arrondissements": None,
    }


def _phone(fragment: str) -> str | None:
    m = _PHONE.search(html.unescape(fragment).replace("\xa0", " "))
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))[:10]
    return " ".join(digits[i : i + 2] for i in range(0, len(digits), 2))


def parse_centres(page: str) -> list[dict]:
    """Every centre of the ANSM list, in page order."""
    centres = []
    for item in _ITEM.findall(page):
        heading = _HEADING.search(item)
        depts = _DEPTS.search(item)
        if not heading or not depts:
            continue
        mail = _MAIL.search(item)
        site = _SITE.search(item)
        centres.append(
            {
                "nom": _text(heading.group(1)),
                "departements": [
                    parse_departement(li) for li in _LI.findall(depts.group(1))
                ],
                "telephone": _phone(item),
                "courriel": mail.group(1).strip() if mail else None,
                "site": site.group(1) if site else None,
            }
        )
    return centres


def main() -> int:
    request = urllib.request.Request(
        SOURCE, headers={"User-Agent": "pharmacovigilance-normandie-build"}
    )
    # Only the fixed https address above is opened.
    with urllib.request.urlopen(request, timeout=60) as response:
        page = response.read().decode("utf-8")
    centres = parse_centres(page)
    if len(centres) < 25:
        raise SystemExit(
            f"fetch_crpv : {len(centres)} centres lus seulement ; la page a-t-elle changé ?"
        )
    data = {
        "source": SOURCE,
        "mis_a_jour": parse_update_date(page),
        # Local date of the machine that ran the fetch (timezone-aware).
        "consulte_le": dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat(),
        "centres": centres,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"{OUT.relative_to(ROOT)} : {len(centres)} centres (liste mise à jour le {data['mis_a_jour']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
