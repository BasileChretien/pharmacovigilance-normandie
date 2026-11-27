"""Fetch the official alerts feed (actualites/posts/alertes-officielles.qmd).

Two fixed pages, read as they are, without rewriting:
- ANSM, "Informations de sécurité" filtered on "Risques médicamenteux": date, product
  family, title, audience and link of each communication;
- EMA, page of the Pharmacovigilance Risk Assessment Committee (PRAC): the latest
  "Meeting highlights", with EMA's own one-line summary.

Writes data/alertes.json. A site that does not answer, or whose page no longer has the
expected shape, keeps its previous list and date, and the script exits with 1 so the
weekly build (.github/workflows/pages.yml) shows a warning. Standard library only: the
build runs it with the runner's python3.

Usage: python tools/build/fetch_alertes.py
Then: python tools/build/make_alertes_page.py
"""

from __future__ import annotations

import datetime as dt
import html
import http.client
import json
import re
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "alertes.json"
USER_AGENT = "pharmacovigilance-normandie-build"

_TAG = re.compile(r"<[^>]+>")
_BREAK = re.compile(r"<br\s*/?>|</?(?:p|div|li)\b[^>]*>", re.IGNORECASE)
_SPACES = re.compile(r"\s+")

_ANSM_ITEM = re.compile(
    r'<article class="article-item article-security".*?</article>', re.DOTALL
)
_ANSM_HREF = re.compile(r'<a href="(/informations-de-securite/[a-z0-9-]+)"')
_EMA_ITEM = re.compile(r'<article class="node ema-news.*?</article>', re.DOTALL)
_EMA_LINK = re.compile(
    r'<h3 class="teaser-title[^"]*">\s*<a class="standalone" href="(/en/news/[a-z0-9-]+)">(.*?)</a>',
    re.DOTALL,
)
_EMA_SUMMARY = re.compile(r'<div class="card-text[^"]*">\s*<p>(.*?)</p>', re.DOTALL)
_EMA_DATE = re.compile(
    r'<div class="metadata-item[^"]*">\s*(\d{1,2}) ([A-Z][a-z]+) (\d{4})\s*<'
)
_MOIS_EN = {
    m: i
    for i, m in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}


def _text(fragment: str | None) -> str | None:
    """Plain text of an HTML fragment, or None when empty."""
    if fragment is None:
        return None
    # A line break becomes a space; other tags (<b>, <i>…) go without adding one.
    fragment = _BREAK.sub(" ", fragment)
    text = _SPACES.sub(" ", html.unescape(_TAG.sub("", fragment))).strip()
    return text or None


def _span(item: str, cls: str) -> str | None:
    m = re.search(rf'<span class="{cls}">(.*?)</span>', item, re.DOTALL)
    return _text(m.group(1)) if m else None


def _iso(day: str, month: str, year: str) -> str:
    return dt.date(int(year), int(month), int(day)).isoformat()


def parse_ansm(page: str) -> list[dict]:
    """ANSM safety communications, in page order (latest first)."""
    items = []
    for item in _ANSM_ITEM.findall(page):
        href = _ANSM_HREF.search(item)
        titre = _span(item, "article-title h5")
        dates = re.findall(
            r"(\d{2})/(\d{2})/(\d{4})", _span(item, "article-date") or ""
        )
        if not (href and titre and dates):
            continue  # off-site link or unknown shape: never shown
        items.append(
            {
                "titre": titre,
                "url": "https://ansm.sante.fr" + href.group(1),
                "publie_le": _iso(*dates[0]),
                "mis_a_jour_le": _iso(*dates[1]) if len(dates) > 1 else None,
                "produit": _span(item, "article-health-product"),
                "public": _span(item, "article-content"),
            }
        )
    return items


def parse_ema(page: str) -> list[dict]:
    """EMA PRAC meeting highlights, in page order (latest first)."""
    items = []
    for item in _EMA_ITEM.findall(page):
        link = _EMA_LINK.search(item)
        date = _EMA_DATE.search(item)
        if not (link and date and date.group(2) in _MOIS_EN):
            continue
        titre = _text(link.group(2))
        if not titre:
            continue  # a card whose link holds only an image: nothing to show
        summary = _EMA_SUMMARY.search(item)
        day, month, year = date.groups()
        items.append(
            {
                "titre": titre,
                "resume": _text(summary.group(1)) if summary else None,
                "url": "https://www.ema.europa.eu" + link.group(1),
                "publie_le": _iso(day, str(_MOIS_EN[month]), year),
            }
        )
    return items


# minimum: fewer items than this means the page has changed, not that alerts stopped.
SOURCES = {
    "ansm": {
        "url": "https://ansm.sante.fr/informations-de-securite/?safety_news_filter%5BsafetyNewsModels%5D%5B%5D=2",
        "parse": parse_ansm,
        "minimum": 5,
        "garder": 12,
    },
    "ema": {
        "url": "https://www.ema.europa.eu/en/committees/pharmacovigilance-risk-assessment-committee-prac",
        "parse": parse_ema,
        "minimum": 1,
        "garder": 4,
    },
}


def refresh(
    previous: dict, fetch: Callable[[str], str], today: str
) -> tuple[dict, list[str]]:
    """New lists for every source that answers; the previous list for the others."""
    data, errors = {}, []
    for key, source in SOURCES.items():
        try:
            items = source["parse"](fetch(source["url"]))
            if len(items) < source["minimum"]:
                raise ValueError(
                    f"{len(items)} alertes lues ; la page a-t-elle changé ?"
                )
        # HTTPException: a connection cut mid-read (IncompleteRead), a bad status line.
        except (OSError, ValueError, http.client.HTTPException) as exc:
            errors.append(f"{key} : {exc}")
            if key in previous:
                data[key] = previous[key]
            continue
        data[key] = {
            "source": source["url"],
            "releve_le": today,
            "alertes": items[: source["garder"]],
        }
    return data, errors


def _fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # Only the fixed https addresses of SOURCES are opened.
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def _date_iso(value: object) -> bool:
    return isinstance(value, str) and _ISO.fullmatch(value) is not None


def _alerte_saine(alerte: object) -> bool:
    """An alert with what the page prints: a title, a link, ISO dates."""
    return (
        isinstance(alerte, dict)
        and isinstance(alerte.get("titre"), str)
        and isinstance(alerte.get("url"), str)
        and _date_iso(alerte.get("publie_le"))
        and (alerte.get("mis_a_jour_le") is None or _date_iso(alerte["mis_a_jour_le"]))
    )


def _bloc_sain(block: object) -> bool:
    """A site's list as refresh() writes it: its address, the date read, its alerts."""
    return (
        isinstance(block, dict)
        and isinstance(block.get("source"), str)
        and _date_iso(block.get("releve_le"))
        and isinstance(block.get("alertes"), list)
        and all(_alerte_saine(a) for a in block["alertes"])
    )


def precedent(path: Path) -> dict:
    """The lists of the previous run, site by site; none if the file is missing or
    damaged, and none for a site whose list has the wrong shape (if that site fails too,
    the page says its list has not been read yet)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: b for k, b in data.items() if k in SOURCES and _bloc_sain(b)}


def main() -> int:
    previous = precedent(OUT)
    # Local date of the machine that ran the fetch (timezone-aware).
    today = dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat()
    data, errors = refresh(previous, _fetch, today)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    for key, block in data.items():
        print(
            f"{key} : {len(block['alertes'])} alertes (relevé le {block['releve_le']})."
        )
    for error in errors:
        print(f"fetch_alertes : {error} ; liste précédente gardée.", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
