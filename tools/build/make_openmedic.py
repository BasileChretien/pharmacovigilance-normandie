"""Reimbursed medicines in Normandy compared with France (normandie/medicaments-rembourses.qmd).

Open Medic (Assurance Maladie, Licence Ouverte): boxes of medicines dispensed in community
pharmacies and reimbursed, by ATC code, age group, sex and region of the beneficiary.
Population: INSEE local estimates (Melodi), mid-year mean of two 1 January estimates.

For each group of medicines linked to a sheet of the site, the number of boxes per 1,000
inhabitants in Normandy (region 28) and in France, crude and standardised on age and sex
(direct method, France as the standard population, 3 age groups x 2 sexes).

Reads the cache written by tools/build/fetch_openmedic.py (data/openmedic/) and writes
data/openmedic-normandie.json and _includes/openmedic-normandie.md (chart and table).

Usage: python tools/build/make_openmedic.py
"""

from __future__ import annotations

import csv
import gzip
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "openmedic"
OUT_DATA = ROOT / "data" / "openmedic-normandie.json"
ANNEE = 2025
NORMANDIE = "28"
FRANCE = "FR"  # every region of Open Medic, overseas and unknown region included
# INSEE geographies: Normandy, and France without Mayotte (its health insurance fund is
# separate from the national schemes covered by Open Medic).
GEOS = {"2026-REG-28": NORMANDIE, "2026-FRANCE-F_X_D976": FRANCE}
SEXES = {"M": "1", "F": "2"}

GROUPES = [
    {
        "cle": "benzodiazepines",
        "libelle": "Benzodiazépines et apparentés",
        "atc": ["N05BA", "N05CD", "N05CF"],
        "fiche": "medicaments/classes/benzodiazepines-apparentes.qmd",
    },
    {
        "cle": "opioides",
        "libelle": "Antalgiques opioïdes",
        "atc": ["N02A"],
        "fiche": "medicaments/classes/opioides.qmd",
    },
    {
        "cle": "antidepresseurs",
        "libelle": "Antidépresseurs",
        "atc": ["N06A"],
        "fiche": "medicaments/classes/antidepresseurs.qmd",
    },
    {
        "cle": "ipp",
        "libelle": "Inhibiteurs de la pompe à protons (IPP)",
        "atc": ["A02BC"],
        "fiche": "medicaments/classes/ipp.qmd",
    },
    {
        "cle": "ains",
        "libelle": "Anti-inflammatoires non stéroïdiens (AINS)",
        "atc": ["M01A"],
        "fiche": "medicaments/classes/ains.qmd",
    },
    {
        "cle": "corticoides",
        "libelle": "Corticoïdes par voie générale",
        "atc": ["H02AB"],
        "fiche": "medicaments/classes/corticoides-oraux.qmd",
    },
    {
        "cle": "statines",
        "libelle": "Statines",
        "atc": ["C10AA"],
        "fiche": "medicaments/classes/statines.qmd",
    },
    {
        "cle": "anticoagulants",
        "libelle": "Anticoagulants oraux",
        "atc": ["B01AA", "B01AF", "B01AE07"],
        "fiche": "medicaments/classes/anticoagulants-oraux.qmd",
    },
    {
        "cle": "antidiabetiques",
        "libelle": "Antidiabétiques",
        "atc": ["A10"],
        "fiche": "medicaments/classes/antidiabetiques.qmd",
    },
    {
        "cle": "levothyroxine",
        "libelle": "Lévothyroxine",
        "atc": ["H03AA01"],
        "fiche": "medicaments/classes/levothyroxine.qmd",
    },
    {
        "cle": "fluoroquinolones",
        "libelle": "Fluoroquinolones",
        "atc": ["J01MA"],
        "fiche": "medicaments/classes/fluoroquinolones.qmd",
    },
    {
        "cle": "antibiotiques",
        "libelle": "Antibiotiques, toutes familles",
        "atc": ["J01"],
        "fiche": None,
    },
]


def tranche(age: str) -> str | None:
    """Open Medic age group ("0", "20", "60") of an INSEE five-year band, None for a total."""
    if age == "Y_LT5":
        return "0"
    if age == "Y_GE95":
        return "60"
    if not age.startswith("Y") or "T" not in age[1:]:
        return None
    debut = int(age[1:].split("T")[0])
    return "0" if debut < 20 else "20" if debut < 60 else "60"


def lire_openmedic(
    path: Path, groupes_atc: dict[str, tuple[str, ...]]
) -> dict[tuple, int]:
    """Boxes by (group, place, sex, age group); place is Normandy or France (every row)."""
    boites: dict[tuple, int] = {}
    with gzip.open(path, "rt", encoding="cp1252", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            atc = row["ATC5"].strip()
            n = int((row["BOITES"] or "0").replace(" ", "").replace(" ", ""))
            for cle, prefixes in groupes_atc.items():
                if atc.startswith(prefixes):
                    places = [FRANCE] + (
                        [NORMANDIE] if row["BEN_REG"].strip() == NORMANDIE else []
                    )
                    for place in places:
                        key = (cle, place, row["sexe"].strip(), row["age"].strip())
                        boites[key] = boites.get(key, 0) + n
    return boites


def population(
    observations: list[dict], annee: int, geos: dict[str, str]
) -> dict[tuple, float]:
    """Mid-year population by (place, sex, age group): mean of 1 January annee and annee + 1."""
    par_annee: dict[tuple, float] = {}
    for o in observations:
        d = o["dimensions"]
        band = tranche(d.get("AGE", "_T"))
        if (
            d.get("EP_MEASURE") != "POP_JAN_1ST"
            or d["GEO"] not in geos
            or d.get("SEX") not in SEXES
            or band is None
        ):
            continue
        year = int(d["TIME_PERIOD"])
        if year not in (annee, annee + 1):
            continue
        key = (geos[d["GEO"]], SEXES[d["SEX"]], band, year)
        par_annee[key] = par_annee.get(key, 0.0) + float(
            o["measures"]["OBS_VALUE_NIVEAU"]["value"]
        )
    pop: dict[tuple, list[float]] = {}
    for (place, sex, band, _year), value in par_annee.items():
        pop.setdefault((place, sex, band), []).append(value)
    return {k: sum(v) / len(v) for k, v in pop.items()}


def taux_standardise(boites: dict, pop: dict, cle: str, place: str) -> float:
    """Boxes per 1,000 inhabitants, standardised on the French population (direct method)."""
    strates = sorted({(s, a) for (p, s, a) in pop if p == FRANCE})
    total = sum(pop[(FRANCE, s, a)] for s, a in strates)
    return 1000 * sum(
        boites.get((cle, place, s, a), 0)
        / pop[(place, s, a)]
        * pop[(FRANCE, s, a)]
        / total
        for s, a in strates
        if pop.get((place, s, a))
    )


def taux_brut(boites: dict, pop: dict, cle: str, place: str) -> float:
    """Every box, unknown age or sex included, per 1,000 inhabitants."""
    n = sum(v for (c, p, _s, _a), v in boites.items() if c == cle and p == place)
    habitants = sum(v for (p, _s, _a), v in pop.items() if p == place)
    return 1000 * n / habitants


def resultats(boites: dict, pop: dict, groupes: list[dict]) -> list[dict]:
    lignes = []
    for g in groupes:
        cle = g["cle"]
        valeurs = {}
        for nom, place in (("normandie", NORMANDIE), ("france", FRANCE)):
            valeurs[nom] = {
                "boites": sum(
                    v for (c, p, _s, _a), v in boites.items() if c == cle and p == place
                ),
                "taux_brut": round(taux_brut(boites, pop, cle, place), 1),
                "taux_standardise": round(taux_standardise(boites, pop, cle, place), 1),
            }
        n, f = (
            valeurs["normandie"]["taux_standardise"],
            valeurs["france"]["taux_standardise"],
        )
        lignes.append(
            {**g, **valeurs, "ecart_pct": round(100 * (n / f - 1)) if f else None}
        )
    return lignes


# --- rendering (French number formats, chart, table, summary) ------------------


def fr_nombre(x: float, decimales: int = 1) -> str:
    """1248.6 -> '1&nbsp;248,6' (non-breaking space for thousands, comma for decimals)."""
    texte = f"{x:,.{decimales}f}"
    return texte.replace(",", "#").replace(".", ",").replace("#", "&nbsp;")


def fr_ecart(pct: int) -> str:
    if pct > 0:
        return f"+{pct}&nbsp;%"
    if pct < 0:
        return f"&minus;{-pct}&nbsp;%"
    return "0&nbsp;%"


def _classees(lignes: list[dict]) -> list[dict]:
    return sorted(lignes, key=lambda ligne: -(ligne["ecart_pct"] or 0))


def graphique(lignes: list[dict], annee: int) -> str:
    """Gap to France per group, as bars either side of a France line. The bars are
    decoration (aria-hidden): each row reads as text, and the table gives every number."""
    plus_grand = max(abs(ligne["ecart_pct"] or 0) for ligne in lignes) or 1
    rows = []
    for ligne in _classees(lignes):
        pct = ligne["ecart_pct"] or 0
        sens = "plus" if pct > 0 else "moins" if pct < 0 else "nul"
        longueur = round(100 * abs(pct) / plus_grand, 1)
        rows.append(
            '<li class="ecart">'
            f'<span class="ecart-nom">{html.escape(ligne["libelle"])}</span>'
            '<span class="ecart-piste" aria-hidden="true">'
            f'<span class="ecart-barre ecart-{sens}" style="--ecart: {longueur}%"></span></span>'
            f'<span class="ecart-valeur">{fr_ecart(pct)}</span></li>'
        )
    return (
        '<figure class="ecarts" aria-labelledby="ecarts-titre">\n'
        f'<figcaption id="ecarts-titre" class="ecarts-titre">Écart de la Normandie à la France en {annee}, '
        "à âge et sexe comparables (boîtes remboursées pour 1&nbsp;000 habitants). "
        "Barre vers la droite : plus qu’en France ; vers la gauche : moins.</figcaption>\n"
        '<p class="ecarts-axe" aria-hidden="true"><span>France</span></p>\n'
        '<ul class="ecarts-liste">\n' + "\n".join(rows) + "\n</ul>\n</figure>"
    )


def tableau(lignes: list[dict], annee: int) -> str:
    """Every number of the chart, and the crude rate, with a link to each sheet."""
    rows = []
    for ligne in _classees(lignes):
        nom = html.escape(ligne["libelle"])
        if ligne.get("fiche"):
            nom = f'<a href="../{html.escape(ligne["fiche"].removesuffix(".qmd"))}.html">{nom}</a>'
        n, f = ligne["normandie"], ligne["france"]
        rows.append(
            f'<tr><th scope="row">{nom}</th><td>{fr_nombre(n["taux_standardise"])}</td>'
            f"<td>{fr_nombre(f['taux_standardise'])}</td><td>{fr_ecart(ligne['ecart_pct'] or 0)}</td>"
            f"<td>{fr_nombre(n['taux_brut'])}</td></tr>"
        )
    # Scrolls sideways on a phone; focusable so the keyboard can scroll it too.
    return (
        '<div class="table-responsive" role="region" aria-label="Chiffres en détail" tabindex="0">\n'
        '<table class="table openmedic-table">\n'
        f"<caption>Boîtes remboursées pour 1&nbsp;000 habitants en {annee}</caption>\n"
        '<thead><tr><th scope="col">Médicaments</th>'
        '<th scope="col">Normandie, à âge et sexe comparables</th>'
        '<th scope="col">France</th><th scope="col">Écart</th>'
        '<th scope="col">Normandie, chiffre brut</th></tr></thead>\n'
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n</div>"
    )


def resume(lignes: list[dict]) -> str:
    """The three largest gaps above France, as a sentence."""
    hauts = [ligne for ligne in _classees(lignes) if (ligne["ecart_pct"] or 0) > 0][:3]
    if not hauts:
        return "<p>Aucun groupe de médicaments n’est plus remboursé en Normandie qu’en France.</p>"
    noms = [
        f"{html.escape(ligne['libelle'][0].lower() + ligne['libelle'][1:])} ({fr_ecart(ligne['ecart_pct'])})"
        for ligne in hauts
    ]
    liste = noms[0] if len(noms) == 1 else ", ".join(noms[:-1]) + " et " + noms[-1]
    return f"<p>Les plus grands écarts au-dessus de la moyenne française : {liste}.</p>"


SOURCES = {
    "openmedic": "https://www.data.gouv.fr/fr/datasets/open-medic-base-complete-sur-les-depenses-de-medicaments-interregimes/",
    "insee": "https://catalogue-donnees.insee.fr/fr/catalogue/recherche/DS_ESTIMATION_POPULATION",
}


def _include(nom: str, contenu: str) -> None:
    (ROOT / "_includes" / f"openmedic-{nom}.md").write_text(
        "<!-- Generated by tools/build/make_openmedic.py from data/openmedic/: "
        "edit the script, not this file. -->\n```{=html}\n" + contenu + "\n```\n",
        encoding="utf-8",
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    fichier = CACHE / f"NB_{ANNEE}_atc5_age_sexe_reg.csv.gz"
    if not fichier.exists() or not (CACHE / "population.json").exists():
        raise SystemExit(
            "make_openmedic : lancez d'abord tools/build/fetch_openmedic.py."
        )
    observations = json.loads((CACHE / "population.json").read_text(encoding="utf-8"))
    pop = population(observations, ANNEE, GEOS)
    boites = lire_openmedic(fichier, {g["cle"]: tuple(g["atc"]) for g in GROUPES})
    lignes = resultats(boites, pop, GROUPES)
    data = {
        "annee": ANNEE,
        "sources": SOURCES,
        "population": {
            "normandie": round(
                sum(v for (p, _s, _a), v in pop.items() if p == NORMANDIE)
            ),
            "france": round(sum(v for (p, _s, _a), v in pop.items() if p == FRANCE)),
        },
        "groupes": lignes,
    }
    OUT_DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    _include("resume", resume(lignes))
    _include("graphique", graphique(lignes, ANNEE))
    _include("tableau", tableau(lignes, ANNEE))
    print(
        f"{OUT_DATA.relative_to(ROOT)} : {len(lignes)} groupes de médicaments ({ANNEE})."
    )
    for ligne in _classees(lignes):
        print(f"  {ligne['libelle']} : {ligne['ecart_pct']:+d} %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
