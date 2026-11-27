"""Fetch the list of Vigiking issues from the site of the French network of regional
pharmacovigilance centres (RFCRPV), for vigiking/archives.qmd.

Per issue: its title (month and year), the month as YYYY-MM, its page and its PDF on
rfcrpv.fr, and its topics as the network lists them. Nothing is copied but these lines:
the PDFs stay on the network's site (links only, until the CRPV agree on hosting).

Writes data/vigiking-archives.json. Run when a new issue is out, then
make_vigiking_page.py.

Usage: python tools/build/fetch_vigiking.py
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "vigiking-archives.json"
SOURCE = "https://www.rfcrpv.fr/bulletins-des-crpv/vigiking-rouen-caen/"
PDF_PREFIX = "https://www.rfcrpv.fr/wp-content/uploads/"
MOIS = {
    m: i
    for i, m in enumerate(
        [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "novembre",
            "décembre",
        ],
        start=1,
    )
}
_ARTICLE = re.compile(r"<article\b.*?</article>", re.DOTALL)
_TITRE = re.compile(r'<h2[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
# The topics: everything from the content block to the footer, whatever its other classes
# or nested blocks ("content" as a whole class: not "content-header" nor "entry-content").
# The PDF: the link of the footer's download button only.
_CONTENU = re.compile(
    r'<div class="(?:[^"]*\s)?content(?:\s[^"]*)?">(.*?)(?=<footer\b|</article>)',
    re.DOTALL,
)
_PIED = re.compile(r"<footer\b.*?</footer>", re.DOTALL)
_PDF = re.compile(r'<a href="([^"]+\.pdf)"', re.IGNORECASE)
# A topic ends at a line break, a paragraph, a list item or a block.
_BREAK = re.compile(r"<br\s*/?>|</p>|</li>|</div>", re.IGNORECASE)
SEPARATEUR = "\x1f"


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _mois(titre: str) -> str | None:
    """'Avril 2025' -> '2025-04'; a double issue takes its first month, and words after the
    year ('Janvier – Février 2020 – Nouvelle formule') do not matter."""
    annee = re.search(r"\b((?:19|20)\d{2})\b", titre)
    premier = next(
        (MOIS[w] for w in re.findall(r"[a-zéû]+", titre.lower()) if w in MOIS), None
    )
    return f"{annee.group(1)}-{premier:02d}" if annee and premier else None


def parse_numeros(page: str) -> list[dict]:
    """Every Vigiking issue of the network's page, in page order (latest first)."""
    numeros = []
    for article in _ARTICLE.findall(page):
        titre = _TITRE.search(article)
        pied = _PIED.search(article)
        pdf = _PDF.search(pied.group(0)) if pied else None
        if not (
            titre
            and pdf
            and titre.group(1).startswith(SOURCE)
            and pdf.group(1).startswith(PDF_PREFIX)
        ):
            continue  # not an issue, or a link off the network's site: never shown
        contenu = _CONTENU.search(article)
        # Entities are decoded first ("d&rsquo;un" holds a ";"), then topics are split on
        # ";" and on the breaks above (marked with a unit separator, as source newlines are
        # just spaces).
        brut = _BREAK.sub(SEPARATEUR, contenu.group(1)) if contenu else ""
        texte = html.unescape(re.sub(r"<[^>]+>", " ", brut))
        parts = re.split(f"[;{SEPARATEUR}]", texte)
        sujets = [s for s in (" ".join(part.split()) for part in parts) if s]
        nom = _text(titre.group(2))
        numeros.append(
            {
                "titre": nom,
                "mois": _mois(nom),
                "page": titre.group(1),
                "pdf": pdf.group(1),
                "sujets": sujets,
            }
        )
    return numeros


def main() -> int:
    request = urllib.request.Request(
        SOURCE, headers={"User-Agent": "pharmacovigilance-normandie-build"}
    )
    # Only the fixed https address above is opened.
    with urllib.request.urlopen(request, timeout=60) as response:
        page = response.read().decode("utf-8")
    numeros = parse_numeros(page)
    if len(numeros) < 10:
        raise SystemExit(
            f"fetch_vigiking : {len(numeros)} numéros lus seulement ; la page a-t-elle changé ?"
        )
    data = {
        "source": SOURCE,
        # Local date of the machine that ran the fetch (timezone-aware).
        "consulte_le": dt.datetime.now(dt.timezone.utc).astimezone().date().isoformat(),
        "numeros": numeros,
    }
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{OUT.relative_to(ROOT)} : {len(numeros)} numéros de Vigiking.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
