"""Official notice and SmPC links for the drug sheets, from the BDPM open files.

For each substance listed in a page's front matter (substances: [...]), picks one
marketed product as an example of its official notice and SmPC: a product with that
substance alone, an oral form first, then the princeps (reference medicine). A page that
cites in its sources (front matter sources:, not the text) a marketed product with that
substance alone gets that product as its own example instead ("pages" in the output;
"pages_lues" names every page that lists substances, so that the filter can warn when a
page's path matches none). It also records the marketing status of every BDPM product
the pages cite, anywhere in the page, so that tools/checks/check_content.py can flag a
product no longer marketed.

Reads the cache written by tools/build/fetch_bdpm.py (data/bdpm/) and writes
data/bdpm-liens.json, read by assets/filters/page-meta.lua ("Notices et RCP officiels").
Prints what needs fixing and exits with 1 if anything does.

Usage: python tools/build/make_bdpm_liens.py
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "bdpm"
OUT = ROOT / "data" / "bdpm-liens.json"
SOURCE = "https://base-donnees-publique.medicaments.gouv.fr/telechargement"
EXCLUDED_DIRS = {
    "_site",
    "_templates",
    "bulletin",  # the Vigiking bulletin, its own Quarto project
    "docs",
    "node_modules",
    ".quarto",
    ".venv",
    "tests",
    "tools",
}
COMMERCIALISEE = "Commercialisée"
_CITE = re.compile(r"base-donnees-publique\.medicaments\.gouv\.fr/medicament/(\d{8})")
_DATE_SPECIALITES = re.compile(
    r'href="/download/file/CIS_bdpm\.txt"[^>]*>.*?(\d{2})/(\d{2})/(\d{4})', re.DOTALL
)


# An inverted salt, maybe followed by words without brackets ('hemihydrate'); a second
# bracket (plant extracts: 'aubepine (extrait d') (fluide)') stays as written.
_INVERSE = re.compile(r"^(.+) \((.+) (de|d')\)((?: [^()]+)?)$")


def normalise(name: str) -> str:
    """Lower case, no accents, single spaces: 'IBUPROFÈNE' -> 'ibuprofene'. A salt written
    the inverted way reads the usual way: 'SODIUM (VALPROATE DE)' -> 'valproate de sodium',
    'CODÉINE (PHOSPHATE DE) HÉMIHYDRATÉ' -> 'phosphate de codeine hemihydrate'."""
    decomposed = unicodedata.normalize("NFKD", name)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    text = " ".join(plain.replace("’", "'").lower().split())
    inverse = _INVERSE.match(text)
    if inverse:
        sel, substance, de, suite = inverse.groups()
        text = f"{substance} {de}{'' if de.endswith(chr(39)) else ' '}{sel}{suite}"
    return text


def _rows(text: str) -> list[list[str]]:
    return [line.split("\t") for line in text.splitlines() if line.strip()]


def _matches(name: str, substance: str) -> bool:
    """The substance as a whole word, at the start or after 'de'/'d'': 'levothyroxine sodique'
    and 'tartrate de zolpidem' match; 'prednisolone' does not match 'predniso'."""
    pattern = rf"(?:^|\bde |\bd')({re.escape(substance)})(?: |$)"
    return re.search(pattern, name) is not None


class Base:
    """The three BDPM files needed: products, compositions, generic groups."""

    def __init__(
        self,
        specialites: dict,
        compositions: dict,
        princeps: set,
        noms: dict | None = None,
    ):
        self.specialites = specialites
        self.compositions = compositions
        self.princeps = princeps
        # Per product, its substances as the BDPM writes them: the active part (FT) when
        # given, else the substance (SA). Used by make_bdpm_recherche.py.
        self.noms = noms or {}

    @classmethod
    def from_texts(cls, specialites: str, compositions: str, generiques: str) -> Base:
        specs = {
            r[0]: {
                "nom": r[1].strip(),
                "voies": r[3],
                "statut": r[4],
                "procedure": r[5],
                "etat": r[6],
            }
            for r in _rows(specialites)
            if len(r) >= 7
        }
        # Per product: (link number, SA or FT, substance name). A substance (SA) and its
        # therapeutic fraction (FT) share a link number.
        compos: dict[str, list[tuple[str, str, str]]] = {}
        groupes: dict[str, dict[str, dict[str, list[str]]]] = {}
        for r in _rows(compositions):
            if len(r) >= 8:
                link, nature, name = r[7].strip(), r[6].strip(), r[3].strip()
                compos.setdefault(r[0], []).append((link, nature, normalise(name)))
                noms = (
                    groupes.setdefault(r[0], {})
                    .setdefault(link, {})
                    .setdefault(nature, [])
                )
                if name not in noms:
                    noms.append(name)
        noms = {}
        for cis, groups in groupes.items():
            names: list[str] = []
            for group in groups.values():
                for name in group.get("FT") or group.get("SA") or []:
                    if name not in names:
                        names.append(name)
            noms[cis] = names
        princeps = {
            r[2] for r in _rows(generiques) if len(r) >= 4 and r[3].strip() == "0"
        }
        return cls(specs, compos, princeps, noms)

    @classmethod
    def from_cache(cls, cache: Path) -> Base:
        # The BDPM files are in Windows-1252.
        def read(name: str) -> str:
            return (cache / name).read_text(encoding="cp1252")

        return cls.from_texts(
            read("CIS_bdpm.txt"), read("CIS_COMPO_bdpm.txt"), read("CIS_GENER_bdpm.txt")
        )

    def commercialise(self, cis: str) -> bool:
        spec = self.specialites.get(cis)
        return (
            bool(spec)
            and spec["statut"] == "Autorisation active"
            and spec["etat"] == COMMERCIALISEE
        )

    @staticmethod
    def _active_parts(comps: list[tuple[str, str, str]]) -> int:
        """Number of active parts: per link number, its FT names if any, else its SA names
        (sacubitril/valsartan is one SA with two FT, so two parts)."""
        groups: dict[str, dict[str, set[str]]] = {}
        for link, nature, name in comps:
            groups.setdefault(link, {}).setdefault(nature, set()).add(name)
        return sum(len(g.get("FT") or g.get("SA") or ()) for g in groups.values())

    def _candidats(self, substance: str, cis_list) -> list[tuple[str, bool]]:
        """Marketed products of cis_list holding the substance, each with 'alone'."""
        wanted = normalise(substance)
        candidates = []
        for cis in cis_list:
            comps = self.compositions.get(cis, [])
            if self.commercialise(cis) and any(
                _matches(name, wanted) for _, _, name in comps
            ):
                candidates.append((cis, self._active_parts(comps) == 1))
        return candidates

    def _rang(self, candidate: tuple[str, bool]) -> tuple:
        """Substance alone first, then an oral form (the sheets are read by patients), then
        the princeps (reference medicine), then by name."""
        cis, alone = candidate
        spec = self.specialites[cis]
        return (
            not alone,
            "orale" not in spec["voies"],
            cis not in self.princeps,
            spec["nom"],
        )

    def _fiche(self, cis: str, alone: bool) -> dict:
        return {
            "cis": cis,
            "nom": self.specialites[cis]["nom"],
            "princeps": cis in self.princeps,
            "association": not alone,
        }

    def choisir(self, substance: str) -> dict | None:
        """The example product for a substance, or None if no marketed product has it."""
        candidates = self._candidats(substance, self.compositions)
        if not candidates:
            return None
        return {**self._fiche(*min(candidates, key=self._rang)), "nb": len(candidates)}

    def exemple_cite(self, substance: str, cites: list[str]) -> dict | None:
        """Among the products a page cites, the marketed one holding the substance alone
        (a combination cited for another substance is no example of this one)."""
        alone = [c for c in self._candidats(substance, cites) if c[1]]
        return self._fiche(*min(alone, key=self._rang)) if alone else None

    def statut(self, cis: str) -> dict | None:
        spec = self.specialites.get(cis)
        return {"nom": spec["nom"], "etat": spec["etat"]} if spec else None


def date_specialites(page: str) -> str | None:
    """ISO update date of the products file, as the download page states it."""
    m = _DATE_SPECIALITES.search(html.unescape(page))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def _front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        return {}
    meta = yaml.safe_load(parts[1]) or {}
    return meta if isinstance(meta, dict) else {}


def _cites_en_sources(meta: dict) -> list[str]:
    """The BDPM products linked from the front matter's sources (url fields)."""
    sources = meta.get("sources")
    urls = (
        [s.get("url") for s in sources if isinstance(s, dict)]
        if isinstance(sources, list)
        else []
    )
    trouves = (_CITE.search(u) for u in urls if isinstance(u, str))
    return list(dict.fromkeys(m.group(1) for m in trouves if m))


def lire_pages(
    root: Path,
) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    """Substances listed by each page; the pages citing each BDPM product anywhere (for
    the marketing check); the pages citing it in their sources (for the page examples)."""
    substances: dict[str, list[str]] = {}
    cites: dict[str, list[str]] = {}
    en_sources: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.qmd")):
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8")
        meta = _front_matter(text)
        listed = meta.get("substances") or []
        if listed:
            substances[rel.as_posix()] = [str(s) for s in listed]
        for cis in dict.fromkeys(_CITE.findall(text)):
            cites.setdefault(cis, []).append(rel.as_posix())
        for cis in _cites_en_sources(meta):
            en_sources.setdefault(cis, []).append(rel.as_posix())
    return substances, cites, en_sources


def construire(
    base: Base,
    substances: dict,
    cites: dict,
    mis_a_jour: str | None,
    en_sources: dict[str, list[str]],
) -> dict:
    """The output: site-wide examples, page examples (from en_sources only), and the
    marketing status of every product in cites.

    en_sources (product -> pages citing it in sources:, the third value of lire_pages)
    has no default: left out, every page would fall back to the site-wide examples
    without notice."""
    choix = {}
    for listed in substances.values():
        for substance in listed:
            found = base.choisir(substance)
            if found:
                choix[substance] = found
    # A page's own example: a product it cites in its sources, when it differs from the
    # site-wide one (the children's sheet cites a suspension, not an adult tablet). A
    # product named in the text (one to avoid, say) is never the example.
    par_page: dict[str, list[str]] = {}
    for cis, pages_citant in en_sources.items():
        for page in pages_citant:
            par_page.setdefault(page, []).append(cis)
    pages: dict[str, dict] = {}
    for page, listed in substances.items():
        for substance in listed:
            exemple = base.exemple_cite(substance, par_page.get(page, []))
            if exemple and exemple["cis"] != (choix.get(substance) or {}).get("cis"):
                pages.setdefault(page, {})[substance] = exemple
    statuts = {
        cis: base.statut(cis) or {"nom": None, "etat": "absent de la base"}
        for cis in sorted(cites)
    }
    return {
        "source": SOURCE,
        "mis_a_jour": mis_a_jour,
        "substances": choix,
        "pages": pages,
        "pages_lues": sorted(substances),
        "cites": statuts,
    }


def rapport(data: dict, substances: dict, cites: dict) -> list[str]:
    problemes = []
    if not data.get("mis_a_jour"):
        # The licence asks for the files' date: the download page has changed shape.
        problemes.append(
            "date des fichiers introuvable sur la page de téléchargement (data/bdpm/telechargement.html)"
        )
    for page, listed in substances.items():
        for substance in listed:
            if substance not in data["substances"]:
                problemes.append(
                    f"{page} : « {substance} » introuvable parmi les médicaments commercialisés"
                )
    for cis, pages in sorted(cites.items()):
        statut = data["cites"].get(cis) or {"nom": None, "etat": "non vérifié"}
        if statut["etat"] != COMMERCIALISEE:
            problemes.append(
                f"{cis} ({statut['nom'] or '?'}) : {statut['etat']} ; cité dans {', '.join(pages)}"
            )
    return problemes


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not (CACHE / "CIS_bdpm.txt").exists():
        raise SystemExit("make_bdpm_liens : lancez d'abord tools/build/fetch_bdpm.py.")
    base = Base.from_cache(CACHE)
    page = CACHE / "telechargement.html"
    mis_a_jour = (
        date_specialites(page.read_text(encoding="utf-8")) if page.exists() else None
    )
    substances, cites, en_sources = lire_pages(ROOT)
    data = construire(base, substances, cites, mis_a_jour, en_sources)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"{OUT.relative_to(ROOT)} : {len(data['substances'])} substances, "
        f"{sum(len(v) for v in data['pages'].values())} exemples propres à une page, "
        f"{len(data['cites'])} médicaments cités (BDPM du {mis_a_jour})."
    )
    problemes = rapport(data, substances, cites)
    for p in problemes:
        print(f"  à corriger : {p}")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())
