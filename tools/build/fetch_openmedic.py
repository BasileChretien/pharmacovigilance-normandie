"""Download the data of normandie/medicaments-rembourses.qmd into data/openmedic/ (a local
cache, not committed):

- Open Medic (Assurance Maladie, Licence Ouverte): boxes by ATC5 code, age group, sex and
  region of the beneficiary, file NB_<year>_atc5_age_sexe_reg.CSV.gz (about 1.3 MB);
- INSEE local population estimates (Melodi API): Normandy and France without Mayotte, by
  sex and five-year age band, on 1 January of the year and of the next one.

Run once a year, when Open Medic publishes a new year, then make_openmedic.py.

Usage: python tools/build/fetch_openmedic.py
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

import make_openmedic as mo

OPENMEDIC = "https://open-data-assurance-maladie.ameli.fr/medicaments/"
MELODI = "https://api.insee.fr/melodi/data/DS_ESTIMATION_POPULATION"
USER_AGENT = "pharmacovigilance-normandie-build"
MIN_BYTES = 200_000


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # Only fixed https addresses of the Assurance Maladie and INSEE are opened.
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def lien_openmedic(page: str, annee: int) -> str:
    """The download link (with its token) of the ATC5 x age x sex x region file."""
    m = re.search(
        rf'href="\./(download_file\.php\?token=[a-f0-9]+&(?:amp;)?file=[^"]*NB_{annee}_atc5_age_sexe_reg\.CSV\.gz)"',
        page,
    )
    if not m:
        raise ValueError(f"lien du fichier NB_{annee}_atc5_age_sexe_reg introuvable")
    return OPENMEDIC + m.group(1).replace("&amp;", "&")


def main() -> int:
    annee = mo.ANNEE
    mo.CACHE.mkdir(parents=True, exist_ok=True)
    page = _get(f"{OPENMEDIC}download2.php?Dir_Rep={annee}_ATC5").decode(
        "utf-8", "replace"
    )
    contenu = _get(lien_openmedic(page, annee))
    if len(contenu) < MIN_BYTES:
        raise SystemExit(
            f"fetch_openmedic : fichier Open Medic de {len(contenu)} octets seulement."
        )
    (mo.CACHE / f"NB_{annee}_atc5_age_sexe_reg.csv.gz").write_bytes(contenu)
    print(
        f"data/openmedic/NB_{annee}_atc5_age_sexe_reg.csv.gz : {len(contenu) // 1024} Ko"
    )

    observations = []
    for geo in mo.GEOS:
        for year in (annee, annee + 1):
            query = urllib.parse.urlencode(
                {
                    "GEO": geo,
                    "EP_MEASURE": "POP_JAN_1ST",
                    "TIME_PERIOD": year,
                    "maxResult": 1000,
                }
            )
            data = json.loads(_get(f"{MELODI}?{query}"))
            found = data.get("observations") or []
            if not found:
                raise SystemExit(
                    f"fetch_openmedic : pas de population INSEE pour {geo} en {year}."
                )
            observations.extend(found)
    (mo.CACHE / "population.json").write_text(
        json.dumps(observations, ensure_ascii=False), encoding="utf-8"
    )
    print(f"data/openmedic/population.json : {len(observations)} observations INSEE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
