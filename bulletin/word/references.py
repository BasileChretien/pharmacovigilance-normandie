"""Number the bracket citations of a Vigiking issue and build its reference list.

Authors type their sources in the text, in square brackets: `[PMID 12345678]`,
`[DOI 10.1136/postgradmedj-2020-138661]`, `[https://doi.org/10.x/y]`, several in one
bracket (`[PMID 1; DOI 10.x/y]`), or `[Réf : free text]` for a source with no identifier.
Each citation becomes a superscript number (`^1^`, `^1,2^`, `^7–10^`), numbered by order
of first appearance, and the list, in Vancouver (NLM) style, is appended as the issue's
last article (before the back cover). Inside a hand-made `::: references` block, an item
that is only a DOI or a PMID is formatted in place.

Metadata come from Crossref (DOI) and PubMed E-utilities (PMID), and are kept in a JSON
cache so that an issue already built can be rebuilt offline. Runs on the Markdown written
by importer.py (brackets escaped as `\\[...\\]`) as well as on hand-written issues.
"""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

AGENT = "vigiking-bulletin/1.0"
DELAI = 10  # seconds
CROSSREF = "https://api.crossref.org/works/"
PUBMED = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    "?db=pubmed&retmode=json&id="
)
NON_TROUVEE = " (référence non trouvée)"
MAX_AUTEURS = 6
MELANGE = (
    "Le texte a déjà des numéros de référence tapés à la main (¹, ^3^ ou une liste "
    "« Références ») en plus des citations entre crochets : les deux numérotations "
    "vont se mélanger. Gardez une seule façon de faire."
)

_DEBUT = r"(?:pmid|doi|<?https?://(?:dx\.)?doi\.org/|r[ée]f\s*[.:])"
# A citation bracket, escaped by pandoc (\[...\]) or not; not a link or a span.
CITATION = re.compile(
    rf"\\?\[\s*(?P<corps>{_DEBUT}[^\[\]\n]*?)\s*\\?\](?![({{])", re.IGNORECASE
)
# Word's hyperlink around a typed doi.org address, inside a citation bracket.
LIEN_DOI = re.compile(
    r"(?i)(\\?\[)\s*\[(https?://(?:dx\.)?doi\.org/[^\]\s]+)\]\(\2\)\s*(\\?\])"
)
REF_LIBRE = re.compile(r"r[ée]f\s*[.:]\s*(?P<texte>.+)", re.IGNORECASE | re.DOTALL)
SEPARATEUR = re.compile(r"(?i)\s*[;,]\s*(?=(?:pmid|doi|<?https?://|10\.|\d))")
_DOI = r"(10\.\d{4,9}/[^\s>]+)"
IDENTIFIANTS = [
    ("pmid", re.compile(r"pmid\s*:?\s*(\d{1,9})", re.IGNORECASE)),
    ("doi", re.compile(rf"doi\s*:?\s*{_DOI}", re.IGNORECASE)),
    ("doi", re.compile(rf"<?https?://(?:dx\.)?doi\.org/{_DOI}>?", re.IGNORECASE)),
    ("doi", re.compile(_DOI)),
]
PMID_NU = re.compile(r"(\d{1,9})")
ECHAPPE = re.compile(r"\\([^A-Za-z0-9\s])")
SPECIAUX = re.compile(r"([\\`*_{}\[\]<>^~$@|#])")
BALISE = re.compile(r"<[^>]+>")
FRONT_MATTER = re.compile(r"\A---\n.*?\n(?:---|\.\.\.)\n", re.DOTALL)
BLOC_REFS = re.compile(r"(?m)^:{3,}\s*(?:references|\{[^}]*\.references\b.*\})\s*$")
FIN_BLOC = re.compile(r"^:{3,}\s*$")
ITEM = re.compile(r"^(\s*\d+\\?\.\s+)(\S.*?)\s*$")
DOS = re.compile(
    r"^(?:\{\{<\s*include\s[^>]*dos\.md\s*>\}\}|#{1,2}\s.*\{[^}]*\.dos\b[^}]*\})\s*$",
    re.MULTILINE,
)
APPEL_MAIN = re.compile(r"(?<![\d^])\^\d[\d,\s–-]*\^|[⁰¹²³⁴⁵⁶⁷⁸⁹]")

Chercher = Callable[[str], dict]


def chercher_web(url: str) -> dict:
    """GET a JSON document; a 404 raises LookupError, a network failure OSError."""
    requete = urllib.request.Request(
        url, headers={"User-Agent": AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(requete, timeout=DELAI) as reponse:
            return json.load(reponse)
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            raise LookupError(url) from erreur
        raise


# --- Reading the citations ---------------------------------------------------


def _desechapper(texte: str) -> str:
    """Undo pandoc's backslash escapes (\\_ \\* \\[ …)."""
    return ECHAPPE.sub(r"\1", texte)


def echapper(texte: str) -> str:
    """Escape Markdown-special characters so that fetched text renders literally."""
    return SPECIAUX.sub(r"\\\1", texte)


def identifiant(texte: str, pmid_nu: bool = False) -> tuple[str, str] | None:
    """Cache key and identifier as typed, for one PMID or DOI; None otherwise."""
    texte = " ".join(_desechapper(texte).split())
    motifs = IDENTIFIANTS + ([("pmid", PMID_NU)] if pmid_nu else [])
    for genre, motif in motifs:
        if trouve := motif.fullmatch(texte):
            valeur = trouve.group(1)
            if genre == "pmid":
                return f"pmid:{int(valeur)}", texte
            doi = urllib.parse.unquote(valeur).rstrip(".,;")
            return f"doi:{doi.lower()}", texte
    return None


def lire_crochet(corps: str) -> list[tuple[str, str]] | None:
    """The (key, as typed) of each source in a bracket; None if it is not understood."""
    libre = REF_LIBRE.fullmatch(corps.strip())
    if libre:
        texte = libre.group("texte").strip()
        return [(f"ref:{' '.join(texte.casefold().split())}", texte)]
    sources = []
    for morceau in SEPARATEUR.split(_desechapper(corps)):
        source = identifiant(morceau, pmid_nu=True)
        if source is None:
            return None
        sources.append(source)
    return sources


def items_manuels(corps: str) -> list[tuple[int, str, str, str]]:
    """Items of hand-made reference blocks that are only an identifier.

    Returns (line index, item prefix, key, as typed).
    """
    lignes, trouves, dedans = corps.split("\n"), [], False
    for i, ligne in enumerate(lignes):
        if BLOC_REFS.match(ligne):
            dedans = True
        elif dedans and FIN_BLOC.match(ligne):
            dedans = False
        elif dedans and (item := ITEM.match(ligne)):
            source = identifiant(item.group(2))
            if source:
                trouves.append((i, item.group(1), *source))
    return trouves


# --- Vancouver formatting ----------------------------------------------------


def _nettoyer(texte: object) -> str:
    """Plain text from a fetched field: no HTML/JATS tags, no entities, one space."""
    if isinstance(texte, list):
        texte = texte[0] if texte else ""
    sans_balises = html.unescape(BALISE.sub("", str(texte or "")))
    return " ".join(sans_balises.split())


def initiales(prenoms: str) -> str:
    """NLM initials: 'Jean-Pierre' -> 'JP', 'Fatima R. N.' -> 'FRN'."""
    parties = re.split(r"[\s.\-‐]+", prenoms)
    return "".join(p[0].upper() for p in parties if p and p[0].isalpha())


def pages_nlm(pages: str) -> str:
    """NLM page range: 452-458 -> 452-8, 1201-1210 -> 1201-10."""
    trouve = re.fullmatch(r"([A-Za-z]*)(\d+)\s*[-–]\s*([A-Za-z]*)(\d+)", pages)
    if not trouve:
        return pages
    prefixe, debut, prefixe_fin, fin = trouve.groups()
    if (prefixe_fin and prefixe_fin != prefixe) or len(fin) != len(debut):
        return pages
    commun = 0
    while commun < len(fin) - 1 and debut[commun] == fin[commun]:
        commun += 1
    return f"{prefixe}{debut}-{fin[commun:]}"


def _phrase(texte: str) -> str:
    return texte if texte.endswith((".", "?", "!")) else texte + "."


def vancouver(meta: dict) -> str:
    """One reference, from cleaned fields (auteurs, titre, revue, annee, volume,
    numero, pages, doi); missing fields are left out."""
    auteurs = meta.get("auteurs") or []
    parties = []
    if auteurs:
        noms = auteurs[:MAX_AUTEURS] + (["et al"] if len(auteurs) > MAX_AUTEURS else [])
        parties.append(_phrase(echapper(", ".join(noms))))
    for champ in ("titre", "revue"):
        if meta.get(champ):
            parties.append(_phrase(echapper(meta[champ].rstrip("."))))
    date = echapper(meta.get("annee") or "")
    if meta.get("volume"):
        date += (";" if date else "") + echapper(meta["volume"])
    if meta.get("numero"):
        date += f"({echapper(meta['numero'])})"
    if meta.get("pages"):
        date += ":" + echapper(pages_nlm(meta["pages"]))
    if date:
        parties.append(date + ".")
    if meta.get("doi"):
        parties.append("doi:" + echapper(meta["doi"]))
    return " ".join(parties)


def _annee_crossref(oeuvre: dict) -> str:
    """The print year (Vancouver cites the issue), else the first one known."""
    numero = (oeuvre.get("journal-issue") or {}).get("published-print")
    dates = [oeuvre.get("published-print"), numero]
    for date in dates + [oeuvre.get("issued"), oeuvre.get("published-online")]:
        parties = (date or {}).get("date-parts") or [[None]]
        if parties[0] and parties[0][0]:
            return str(parties[0][0])
    return ""


def _auteur_crossref(auteur: dict) -> str:
    if auteur.get("family"):
        nom = _nettoyer(auteur["family"])
        init = initiales(_nettoyer(auteur.get("given", "")))
        return f"{nom} {init}".strip()
    return _nettoyer(auteur.get("name", ""))


def depuis_crossref(oeuvre: dict) -> dict:
    """Vancouver fields from a Crossref work (the 'message' of /works/{doi})."""
    titre = _nettoyer(oeuvre.get("title"))
    sous_titre = _nettoyer(oeuvre.get("subtitle"))
    if titre and sous_titre:
        titre = f"{titre.rstrip(':')}: {sous_titre}"
    abrege = _nettoyer(oeuvre.get("short-container-title")).replace(".", "")
    return {
        "auteurs": [n for n in map(_auteur_crossref, oeuvre.get("author", [])) if n],
        "titre": titre,
        "revue": abrege or _nettoyer(oeuvre.get("container-title")),
        "annee": _annee_crossref(oeuvre),
        "volume": _nettoyer(oeuvre.get("volume")),
        "numero": _nettoyer(oeuvre.get("issue")),
        "pages": _nettoyer(oeuvre.get("page") or oeuvre.get("article-number")),
        "doi": _nettoyer(oeuvre.get("DOI")),
    }


def depuis_pubmed(resume: dict) -> dict:
    """Vancouver fields from one PubMed esummary record."""
    auteurs = [
        _nettoyer(a.get("name"))
        for a in resume.get("authors", [])
        if a.get("authtype", "Author") in ("Author", "CollectiveName")
    ]
    ids = {i.get("idtype"): i.get("value") for i in resume.get("articleids", [])}
    annee = re.search(r"\d{4}", resume.get("pubdate") or "")
    return {
        "auteurs": [a for a in auteurs if a],
        "titre": _nettoyer(resume.get("title")),
        "revue": _nettoyer(resume.get("source")),
        "annee": annee.group(0) if annee else "",
        "volume": _nettoyer(resume.get("volume")),
        "numero": _nettoyer(resume.get("issue")),
        "pages": _nettoyer(resume.get("pages")),
        "doi": _nettoyer(ids.get("doi")),
    }


# --- Fetching, with the cache ------------------------------------------------


def lire_cache(cache: Path) -> tuple[dict, list[str]]:
    if not cache.is_file():
        return {}, []
    try:
        donnees = json.loads(cache.read_text(encoding="utf-8"))
        if isinstance(donnees, dict):
            return donnees, []
    except (OSError, ValueError):
        pass
    return {}, [
        "Le fichier des références déjà trouvées était illisible ; il est refait."
    ]


def ecrire_cache(cache: Path, entrees: dict) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    contenu = json.dumps(entrees, ensure_ascii=False, indent=1, sort_keys=True)
    cache.write_text(contenu + "\n", encoding="utf-8")


def _entree(meta: dict) -> dict:
    return {"reference": vancouver(meta), "doi": meta.get("doi", "").lower() or None}


def _chercher_pubmed(pmids: list[str], chercher: Chercher) -> dict:
    """Cache entries for the PMIDs found, in one batched call."""
    try:
        reponse = chercher(PUBMED + ",".join(pmids))
    except LookupError:
        return {}
    reponse = reponse.get("result", {}) if isinstance(reponse, dict) else {}
    trouves = {}
    for pmid in pmids:
        resume = reponse.get(pmid)
        if isinstance(resume, dict) and not resume.get("error") and resume.get("title"):
            trouves[f"pmid:{pmid}"] = _entree(depuis_pubmed(resume))
    return trouves


def _chercher_doi(doi: str, chercher: Chercher) -> dict | None:
    try:
        reponse = chercher(CROSSREF + urllib.parse.quote(doi, safe="/"))
    except LookupError:
        return None
    oeuvre = reponse.get("message") if isinstance(reponse, dict) else None
    return _entree(depuis_crossref(oeuvre)) if isinstance(oeuvre, dict) else None


def chercher_tout(
    cles: list[str], connues: dict, chercher: Chercher
) -> tuple[dict, list[str]]:
    """Fetch the keys missing from the cache; return (new entries, keys not checked
    because the network is down)."""
    nouvelles, faites = {}, set()
    manque = [c for c in cles if c not in connues]
    pmids = [c[5:] for c in manque if c.startswith("pmid:")]
    dois = [c[4:] for c in manque if c.startswith("doi:")]
    try:
        if pmids:
            nouvelles.update(_chercher_pubmed(pmids, chercher))
            faites.update(f"pmid:{p}" for p in pmids)
        for doi in dois:
            entree = _chercher_doi(doi, chercher)
            faites.add(f"doi:{doi}")
            if entree:
                nouvelles[f"doi:{doi}"] = entree
    except (OSError, ValueError):
        # Network down (or an unreadable answer): stop asking, keep what came back.
        return nouvelles, [c for c in manque if c not in faites]
    return nouvelles, []


# --- Putting it together -----------------------------------------------------


def exposant(numeros: list[int]) -> str:
    """Markdown superscript: [1, 2] -> ^1,2^ ; [7, 8, 9, 10] -> ^7–10^."""
    tries, groupes = sorted(set(numeros)), []
    for n in tries:
        if groupes and n == groupes[-1][-1] + 1:
            groupes[-1].append(n)
        else:
            groupes.append([n])
    morceaux = [
        f"{g[0]}–{g[-1]}" if len(g) >= 3 else ",".join(map(str, g)) for g in groupes
    ]
    return "^" + ",".join(morceaux) + "^"


def _groupes(corps: str) -> tuple[list[tuple[int, int, list]], list[str]]:
    """Citation brackets side by side, merged: (start, end, sources)."""
    groupes, avertissements = [], []
    for trouve in CITATION.finditer(corps):
        sources = lire_crochet(trouve.group("corps"))
        if sources is None:
            avertissements.append(
                f"Citation non comprise : [{_desechapper(trouve.group('corps'))}] — "
                "écrivez par exemple [PMID 12345678] ou [DOI 10.xxxx/yyyy]."
            )
            continue
        debut = trouve.start()
        if groupes and not corps[groupes[-1][1] : debut].strip(" \t"):
            groupes[-1] = (groupes[-1][0], trouve.end(), groupes[-1][2] + sources)
        else:
            while debut > 0 and corps[debut - 1] in " \t":
                debut -= 1
            groupes.append((debut, trouve.end(), sources))
    return groupes, avertissements


def _texte_entree(cle: str, tape: str, trouvees: dict) -> str:
    if cle.startswith("ref:"):
        return tape
    entree = trouvees.get(cle)
    return entree["reference"] if entree else echapper(tape) + NON_TROUVEE


def _numeroter(groupes: list, trouvees: dict) -> tuple[list[list[int]], list[str]]:
    """Numbers of each group's sources, and the list entries in order."""
    numeros, liste, par_groupe = {}, [], []
    for _, _, sources in groupes:
        appels = []
        for cle, tape in sources:
            doi = (trouvees.get(cle) or {}).get("doi")
            canonique = f"doi:{doi}" if doi else cle
            if canonique not in numeros:
                liste.append(_texte_entree(cle, tape, trouvees))
                numeros[canonique] = len(liste)
            appels.append(numeros[canonique])
        par_groupe.append(appels)
    return par_groupe, liste


def _ajouter_liste(corps: str, liste: list[str]) -> str:
    """The reference list as the issue's last article, before the back cover."""
    lignes = "\n".join(f"{i}. {texte}" for i, texte in enumerate(liste, 1))
    bloc = f"## Références {{.references-page}}\n\n::: {{.references}}\n{lignes}\n:::\n"
    dos = DOS.search(corps)
    if dos:
        avant = corps[: dos.start()].rstrip("\n")
        return f"{avant}\n\n{bloc}\n{corps[dos.start() :]}"
    return f"{corps.rstrip(chr(10))}\n\n{bloc}"


def _avertir_echecs(cles: dict, trouvees: dict, hors_ligne: list[str]) -> list[str]:
    messages = []
    # A DOI not found by Crossref but given by PubMed for a cited PMID is covered.
    dois = {
        f"doi:{trouvees[c]['doi']}" for c in cles if (trouvees.get(c) or {}).get("doi")
    }
    for cle, tape in cles.items():
        if cle.startswith("ref:") or cle in trouvees or cle in {*hors_ligne, *dois}:
            continue
        quoi = "le numéro" if cle.startswith("pmid:") else "le DOI"
        messages.append(f"Référence introuvable : {tape} — vérifiez {quoi}.")
    if hors_ligne:
        noms = ", ".join(cles[c] for c in hors_ligne)
        verbe = (
            "n'a pas pu être vérifiée"
            if len(hors_ligne) == 1
            else "n'ont pas pu être vérifiées"
        )
        messages.append(f"Pas de connexion internet : {noms} {verbe}.")
    return messages


def _remplacer(
    corps: str, groupes: list, appels: list, manuels: list, trouvees: dict
) -> str:
    lignes = corps.split("\n")
    for i, prefixe, cle, tape in manuels:
        lignes[i] = prefixe + _texte_entree(cle, tape, trouvees)
    corps = "\n".join(lignes)
    for (debut, fin, _), numeros in reversed(list(zip(groupes, appels))):
        corps = corps[:debut] + exposant(numeros) + corps[fin:]
    return corps


def resoudre(
    texte: str, cache: Path, chercher: Chercher | None = None
) -> tuple[str, list[str]]:
    """Return (new Markdown text, warnings in plain French)."""
    chercher = chercher or chercher_web
    entete = FRONT_MATTER.match(texte)
    tete, corps = (entete.group(0), texte[entete.end() :]) if entete else ("", texte)
    corps = LIEN_DOI.sub(r"\1\2\3", corps)
    groupes, avertissements = _groupes(corps)
    manuels = items_manuels(corps)
    if not groupes and not manuels:
        return texte, avertissements
    if groupes and (APPEL_MAIN.search(corps) or BLOC_REFS.search(corps)):
        avertissements.append(MELANGE)
    cles = {c: t for _, _, s in groupes for c, t in s}
    cles.update({c: t for *_, c, t in manuels})
    connues, alerte_cache = lire_cache(cache)
    a_chercher = [c for c in cles if not c.startswith("ref:")]
    nouvelles, hors_ligne = chercher_tout(a_chercher, connues, chercher)
    trouvees = {**connues, **nouvelles}
    if nouvelles:
        ecrire_cache(cache, trouvees)
    appels, liste = _numeroter(groupes, trouvees)
    corps = _remplacer(corps, groupes, appels, manuels, trouvees)
    if liste:
        corps = _ajouter_liste(corps, liste)
    avertissements += alerte_cache + _avertir_echecs(cles, trouvees, hors_ligne)
    return tete + corps, avertissements
