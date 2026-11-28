"""Fetch the recent publications of the two CRPV teams (crpv/recherche.qmd).

Whose: the members whose card on crpv/equipe-caen.qmd or crpv/equipe-rouen.qmd gives an
ORCID iD. A card is published only with the member's written consent, so the list follows
the cards: no card, no publications, and a card taken down takes its works with it.

How: ORCID's public API gives each member's works as the member lists them (those with a
DOI); OpenAlex gives, by DOI, the title, the journal, the date, the language, free access
and retraction. Works of the current year and the ANNEES - 1 before, of the types in
TYPES, are kept; a work two members list appears once, under both teams.

Writes data/publications.json, with the members whose works could not be read
("non_lus"): a member whose ORCID record is missing, locked or deactivated, or whose card
links to orcid.org without a valid iD (the log names the page). The others are listed.
When ORCID or OpenAlex does not answer at all, the previous list is kept, without the
works of members whose card has gone, and a member it never read counts as not read.
Either way the script exits with 1, so the build (.github/workflows/pages.yml) shows a
warning; the page says how many members' works are missing. Standard library only: the
build runs it with the runner's python3. An OpenAlex API key in the environment variable
OPENALEX_API_KEY is used if set; without one, requests share OpenAlex's free daily budget,
which is enough for a few members.

Usage: python tools/build/fetch_publications.py
Then: python tools/build/make_publications_page.py
"""

from __future__ import annotations

import datetime as dt
import html
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "publications.json"
EQUIPES = {"caen": "crpv/equipe-caen.qmd", "rouen": "crpv/equipe-rouen.qmd"}
USER_AGENT = "pharmacovigilance-normandie-build"
ORCID_API = "https://pub.orcid.org/v3.0/{}/works"
OPENALEX_API = "https://api.openalex.org/works"
ANNEES = 3
# OpenAlex work types listed; preprints, datasets, errata and peer reviews are left out.
TYPES = {"article", "review", "letter", "editorial", "book-chapter"}
PAR_REQUETE = 50  # DOIs per OpenAlex request
SELECT = "doi,display_name,publication_date,type,language,primary_location,open_access,is_retracted"

# ORCID answers these for a record that is missing, locked or deactivated: that member is
# not read, the others are. Any other failure, or one of these for every member (ORCID
# retiring its API version), is an outage and fails the whole run.
FICHE_ABSENTE = {404, 409, 410}

# What follows orcid.org/ in a card's link, read loosely so that a mistyped iD is reported
# rather than skipped; then checked against _ID and the check digit.
_ORCID = re.compile(r"https?://(?:www\.)?orcid\.org/([^\s/)\]\"'<>?#]+)")
# Punctuation that may follow a link in a sentence or close its bold: not part of an iD.
_APRES_LIEN = ".,;:!*_"
_ID = re.compile(r"[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]")
_PREFIXE_DOI = re.compile(r"(?:https?://)?(?:dx\.)?doi\.org/|doi:\s*", re.IGNORECASE)
_COMMENTAIRE = re.compile(r"<!--.*?-->", re.DOTALL)
_DOI = re.compile(r"10\.[0-9]{4,9}/\S+")
_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")
# ASCII digits only: \d would also take other scripts' digits.
_ISO = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_LANGUE = re.compile(r"[a-z]{2,3}")


def orcid_valide(orcid: str) -> bool:
    """The ORCID check digit (ISO 7064 11,2) matches."""
    chiffres = orcid.replace("-", "")
    total = 0
    for c in chiffres[:-1]:
        total = (total + int(c)) * 2
    reste = (12 - total % 11) % 11
    return chiffres[-1] == ("X" if reste == 10 else str(reste))


def membres(
    root: Path = ROOT,
) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """ORCID iD -> its teams, from the member cards of the two team pages (a card left in
    an HTML comment does not count); and the orcid.org links that give no valid iD, with
    their page. A lower-case check digit x is read as X."""
    trouves: dict[str, list[str]] = {}
    illisibles: list[tuple[str, str]] = []
    for equipe, chemin in EQUIPES.items():
        texte = _COMMENTAIRE.sub("", (root / chemin).read_text(encoding="utf-8"))
        for lien in _ORCID.findall(texte):
            brut = lien.rstrip(_APRES_LIEN)
            orcid = brut.upper()
            if not (_ID.fullmatch(orcid) and orcid_valide(orcid)):
                if (chemin, brut) not in illisibles:
                    illisibles.append((chemin, brut))
                continue
            equipes = trouves.setdefault(orcid, [])
            if equipe not in equipes:
                equipes.append(equipe)
    return trouves, illisibles


def normaliser_doi(valeur: str) -> str | None:
    """A DOI in lower case without its prefix, or None. A DOI holding a comma or a bar is
    left out: OpenAlex's filter would read it as two."""
    doi = valeur.strip()
    prefixe = _PREFIXE_DOI.match(doi)
    if prefixe:
        doi = doi[prefixe.end() :]
        if "doi.org" in prefixe.group(0).lower():
            # A link may encode the slash: 10.1002%2Fpds.
            doi = urllib.parse.unquote(doi)
    doi = doi.strip().lower()
    if not _DOI.fullmatch(doi) or "," in doi or "|" in doi:
        return None
    return doi


def _annee(resume: object) -> int | None:
    if not isinstance(resume, dict):
        return None
    valeur = ((resume.get("publication-date") or {}).get("year") or {}).get("value")
    return int(valeur) if isinstance(valeur, str) and valeur.isdigit() else None


def _doi_du_groupe(groupe: dict) -> str | None:
    """A group's first usable DOI of its own, ORCID's normalised form first."""
    for eid in (groupe.get("external-ids") or {}).get("external-id") or []:
        if (
            eid.get("external-id-type") != "doi"
            or eid.get("external-id-relationship") != "self"
        ):
            continue
        normalise = (eid.get("external-id-normalized") or {}).get("value")
        for valeur in (normalise, eid.get("external-id-value")):
            doi = normaliser_doi(valeur) if isinstance(valeur, str) else None
            if doi:
                return doi
    return None


def dois_orcid(reponse: dict, depuis: int) -> list[str]:
    """The DOIs of the works an ORCID record lists (one per group of versions of a work),
    but those whose latest ORCID date is before the year depuis (undated ones are kept)."""
    dois = []
    for groupe in reponse.get("group") or []:
        annees = [a for a in map(_annee, groupe.get("work-summary") or []) if a]
        if annees and max(annees) < depuis:
            continue
        doi = _doi_du_groupe(groupe)
        if doi and doi not in dois:
            dois.append(doi)
    return dois


def _texte(fragment: object) -> str | None:
    """Plain text of a title or a journal name (OpenAlex keeps some <i> tags)."""
    if not isinstance(fragment, str):
        return None
    texte = _SPACES.sub(" ", html.unescape(_TAG.sub("", fragment))).strip()
    return texte or None


def _date_iso(valeur: object) -> bool:
    """A real date written YYYY-MM-DD: '2026-99-99' is refused."""
    if not (isinstance(valeur, str) and _ISO.fullmatch(valeur)):
        return False
    try:
        dt.date.fromisoformat(valeur)
    except ValueError:
        return False
    return True


def _url_web(valeur: object) -> str | None:
    if isinstance(valeur, str) and valeur.startswith(("https://", "http://")):
        return valeur
    return None


def notice(oeuvre: dict, auteurs: dict[str, list[str]]) -> dict | None:
    """What the page prints of an OpenAlex work, or None for a type not listed or a work
    without a title or a date. auteurs: ORCID iD -> teams of the members who list it."""
    doi = normaliser_doi(oeuvre.get("doi") or "")
    titre = _texte(oeuvre.get("display_name"))
    date = oeuvre.get("publication_date")
    if oeuvre.get("type") not in TYPES or not (doi and titre and _date_iso(date)):
        return None
    source = (oeuvre.get("primary_location") or {}).get("source") or {}
    libre = oeuvre.get("open_access") or {}
    langue = oeuvre.get("language")
    return {
        "doi": doi,
        "titre": titre,
        "revue": _texte(source.get("display_name")),
        "publie_le": date,
        "langue": langue
        if isinstance(langue, str) and _LANGUE.fullmatch(langue)
        else None,
        "acces_libre": _url_web(libre.get("oa_url")) if libre.get("is_oa") else None,
        "retracte": oeuvre.get("is_retracted") is True,
        "membres": sorted(auteurs),
        "equipes": sorted({e for equipes in auteurs.values() for e in equipes}),
    }


def _url_openalex(dois: list[str], depuis: int, cle: str | None) -> str:
    params = {
        "filter": f"doi:{'|'.join(dois)},from_publication_date:{depuis}-01-01",
        "select": SELECT,
        "per-page": str(2 * PAR_REQUETE),
    }
    if cle:
        params["api_key"] = cle
    return OPENALEX_API + "?" + urllib.parse.urlencode(params)


def releve(
    equipes: dict[str, list[str]],
    fetch: Callable[[str], dict],
    aujourd_hui: dt.date,
    cle: str | None = None,
) -> dict:
    """The list read now from ORCID then OpenAlex; a member whose ORCID record is
    missing, locked or deactivated is not read (non_lus). Raises OSError, ValueError,
    TypeError, AttributeError or HTTPException when a site does not answer as expected."""
    depuis = aujourd_hui.year - ANNEES + 1
    par_doi: dict[str, dict[str, list[str]]] = {}
    non_lus = []
    for orcid, siennes in equipes.items():
        try:
            reponse = fetch(ORCID_API.format(orcid))
        except urllib.error.HTTPError as exc:
            if exc.code not in FICHE_ABSENTE:
                raise
            non_lus.append(orcid)
            if len(non_lus) == len(equipes):
                raise  # no member read at all: the API, not the records
            continue
        for doi in dois_orcid(reponse, depuis):
            par_doi.setdefault(doi, {})[orcid] = siennes
    publications: dict[str, dict] = {}
    dois = sorted(par_doi)
    for i in range(0, len(dois), PAR_REQUETE):
        reponse = fetch(_url_openalex(dois[i : i + PAR_REQUETE], depuis, cle))
        for oeuvre in reponse.get("results") or []:
            doi = normaliser_doi(oeuvre.get("doi") or "")
            n = notice(oeuvre, par_doi.get(doi, {})) if doi in par_doi else None
            if n and doi not in publications:
                publications[doi] = n
    return {
        "releve_le": aujourd_hui.isoformat(),
        "depuis": depuis,
        "membres": sorted(equipes),
        "non_lus": sorted(non_lus),
        "publications": sorted(
            publications.values(),
            key=lambda p: (p["publie_le"], p["titre"]),
            reverse=True,
        ),
    }


def _notice_saine(p: object) -> bool:
    return (
        isinstance(p, dict)
        and all(isinstance(p.get(k), str) for k in ("doi", "titre"))
        and _date_iso(p.get("publie_le"))
        and all(
            isinstance(p.get(k), (str, type(None)))
            for k in ("revue", "langue", "acces_libre")
        )
        and isinstance(p.get("retracte"), bool)
        and all(isinstance(p.get(k), list) for k in ("membres", "equipes"))
    )


def _textes(valeur: object) -> bool:
    return isinstance(valeur, list) and all(isinstance(v, str) for v in valeur)


def precedent(path: Path, equipes: dict[str, list[str]]) -> dict | None:
    """The previous list, without the works of members whose card has gone; a member it
    did not read (not on the cards then, or not read then) counts as not read. None if
    the file is missing or damaged."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not (
        isinstance(data, dict)
        and _date_iso(data.get("releve_le"))
        and isinstance(data.get("depuis"), int)
        and _textes(data.get("membres"))
        and _textes(data.get("non_lus", []))
        and isinstance(data.get("publications"), list)
        and all(_notice_saine(p) for p in data["publications"])
    ):
        return None
    lus = set(data["membres"]) - set(data.get("non_lus", []))
    gardees = []
    for p in data["publications"]:
        restants = sorted(set(p["membres"]) & set(equipes))
        if restants:
            teams = sorted({e for m in restants for e in equipes[m]})
            gardees.append({**p, "membres": restants, "equipes": teams})
    return {
        **data,
        "membres": sorted(equipes),
        "non_lus": sorted(set(equipes) - lus),
        "publications": gardees,
    }


def non_releve(equipes: dict[str, list[str]]) -> dict:
    """No list yet: the sites failed and there is no sound previous list."""
    return {
        "releve_le": None,
        "depuis": None,
        "membres": sorted(equipes),
        "non_lus": sorted(equipes),
        "publications": [],
    }


def _ecrire(data: dict) -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def _fetch(url: str) -> dict:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    # Only the fixed https addresses of ORCID_API and OPENALEX_API are opened.
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise TypeError("réponse inattendue")
    return data


def avec_illisibles(data: dict, illisibles: list[tuple[str, str]]) -> dict:
    """A card whose orcid.org link gives no valid iD counts as a member not read."""
    bruts = {brut for _, brut in illisibles}
    return {
        **data,
        "membres": sorted(set(data["membres"]) | bruts),
        "non_lus": sorted(set(data["non_lus"]) | bruts),
    }


def main() -> int:
    equipes, illisibles = membres()
    for chemin, brut in illisibles:
        print(
            f"fetch_publications : lien ORCID sans identifiant valide dans {chemin} : "
            f"{brut} ; ce membre n'est pas relevé.",
            file=sys.stderr,
        )
    # Local date of the machine that ran the fetch (timezone-aware).
    today = dt.datetime.now(dt.timezone.utc).astimezone().date()
    panne = False
    try:
        data = releve(equipes, _fetch, today, os.environ.get("OPENALEX_API_KEY"))
    # HTTPException: a connection cut mid-read (IncompleteRead), a bad status line;
    # TypeError, AttributeError: an answer of an unexpected shape. The message never
    # holds the address, which may carry the API key.
    except (
        OSError,
        ValueError,
        TypeError,
        AttributeError,
        http.client.HTTPException,
    ) as exc:
        panne = True
        code = getattr(exc, "code", None)
        print(
            f"fetch_publications : ORCID ou OpenAlex n'a pas répondu "
            f"({type(exc).__name__}{f' {code}' if code else ''}) ; liste précédente gardée.",
            file=sys.stderr,
        )
        data = precedent(OUT, equipes) or non_releve(equipes)
    sans_fiche = sorted(set(data["non_lus"]) & set(equipes))
    if sans_fiche and not panne:
        print(
            "fetch_publications : fiche ORCID introuvable, verrouillée ou non publique : "
            + ", ".join(sans_fiche),
            file=sys.stderr,
        )
    data = avec_illisibles(data, illisibles)
    _ecrire(data)
    print(
        f"{OUT.name} : {len(data['publications'])} publications ; "
        f"{len(data['membres']) - len(data['non_lus'])} membres relevés sur "
        f"{len(data['membres'])} (depuis {data['depuis']})."
    )
    return 1 if panne or data["non_lus"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
