"""Check a Vigiking issue before it is sent: the author's to-do list.

Four checks, each returning alerts (Alerte): the Word file as written (verifier_docx),
the imported issue (verifier_numero), the page measures reported by the PDF template
(verifier_mesures) and the links of the issue (verifier_liens, addresses from liens()).
rapport() turns the alerts into plain French text for the console and the report file.

Every message says where (article, picture, page) and what to do, in plain words: the
readers are pharmacologists, not typesetters. Standard library only.
"""

from __future__ import annotations

import re
import socket
import struct
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from xml.etree import ElementTree as ET

# Alert level -> (report section, line mark), in report order.
SECTIONS = {
    "corriger": ("À corriger", "✖"),
    "verifier": ("À vérifier", "⚠"),
    "info": ("Pour information", "ℹ"),
}
ALT = "clic droit sur l'image → Modifier le texte de remplacement"
MESSAGES = {
    "sous-titre": "Le sous-titre manque : écrivez le mois du numéro (par exemple "
    "« Octobre 2025 ») sur une ligne au style « Sous-titre », sous le titre.",
    "couleur": "{lieu} : couleur mise à la main sur {quoi} — elle sera perdue. Pour "
    "une mise en garde, utilisez le style « Bloc Attention » ; pour un médicament dans une "
    "liste, « Contre-indication » (rouge) ou « CredibleMeds » (orange).",
    "fond": "{lieu} : fond coloré mis à la main sur {quoi} — il sera perdu. Utilisez le "
    "style « Encadré » (encadré bleu) ou un style « Catégorie … ».",
    "image": "{lieu} : {quoi} {plus} pas de texte de remplacement, lu par les lecteurs d'écran "
    f"(dans Word : {ALT}).",
    "style": "{lieu} : le style « {quoi} »{plus} ne fait pas partie du modèle — sa mise "
    "en forme sera perdue. Utilisez un style du modèle (« Encadré », un « Bloc … », "
    "« Légende », « Catégorie … ») ou « Normal » ; pour un encadré de couleur à vous, "
    "renommez le style « Bloc » suivi de son titre (par exemple « Bloc Interaction »).",
    "styles": "… et {quoi} autre(s) style(s) hors du modèle, à remplacer de même.",
    "auteur": "{lieu} : le nom de l'auteur est à compléter (ligne « Auteur : Initiale. "
    "Nom » sous le titre). Il ne s'affiche qu'avec l'accord écrit de l'auteur.",
    "auteur modele": "{lieu} : le nom de l'auteur est encore celui du modèle (« {quoi} ») : "
    "remplacez-le par le vrai nom, ou retirez la ligne « Auteur : ».",
    "ligne egaree": "{lieu} : la ligne « {quoi} » s'affiche dans le texte de l'article. Les "
    "lignes « Auteur : », « Rubrique : » et « Relecture : » se placent juste sous le "
    "« Titre 1 », avant tout « Titre 2 » ; pour un nouvel article, utilisez « Titre 1 ».",
    "rubrique": "{lieu} : la rubrique « {quoi} » n'est pas une des trois habituelles "
    "(Cas d'ici et d'ailleurs, Littérature, Infos des Autorités de Santé) : vérifiez son "
    "orthographe ; elle fait un groupe à part dans le sommaire.",
    "a completer": "{lieu} : il reste {quoi} dans le texte ; complétez-le ou retirez-le.",
    "introuvable": "{lieu} : {quoi} est introuvable ({plus}) ; remettez-la dans le "
    "fichier Word et refaites l'import.",
    "format": "{lieu} : {quoi} est au format {plus}, que le PDF et la page web "
    "n'affichent pas. Remplacez-la dans Word par une image PNG ou JPEG.",
    "petite": "{lieu} : {quoi} est petite ({plus} de large) et peut paraître "
    "floue. Demandez-en une version plus grande (au moins 800 pixels de large).",
    "sans couverture": "Pas d'image de couverture : une couverture graphique est créée "
    "à la place. Pour mettre une image, placez-la dans Word avant le premier article.",
    "deborde": "{lieu} : trop long pour sa page, même en petits caractères (les images "
    "comptent aussi). Raccourcissez-le, réduisez une image, ou coupez-le en deux articles "
    "(un nouveau « Titre 1 »).",
    "petit texte": "{lieu} : texte en petits caractères ({quoi} pt) ; un texte plus "
    "court se lirait mieux.",
    "lien mort": "Lien mort : {lieu} ({quoi}). Corrigez l'adresse ou retirez le lien.",
    "lien": "Lien à vérifier : {lieu} ({quoi}). Ouvrez-le pour vous assurer qu'il marche.",
    "hors ligne": "Les liens n'ont pas été vérifiés : pas de connexion Internet.",
}


@dataclass(frozen=True)
class Alerte:
    """One point for the author: "corriger" (must fix), "verifier" (to check), "info"."""

    niveau: str
    message: str

    def __post_init__(self) -> None:
        if self.niveau not in SECTIONS:
            raise ValueError(f"niveau d'alerte inconnu : {self.niveau!r}")


def _alerte(
    niveau: str, cle: str, lieu: str = "", quoi: object = "", plus: object = ""
) -> Alerte:
    return Alerte(niveau, MESSAGES[cle].format(lieu=lieu, quoi=quoi, plus=plus))


def _extrait(texte: str, n: int = 40) -> str:
    """Text on one line, cut to n characters."""
    texte = " ".join(texte.split())
    return texte if len(texte) <= n else texte[: n - 1].rstrip() + "…"


def _liste(extraits: list[str], unite: str) -> str:
    """« a », « b » et 2 autres <unite>s: at most three distinct quoted excerpts."""
    vus = list(dict.fromkeys(extraits))
    reste = len(vus) - 3
    suite = f" et {reste} autre{'s' * (reste > 1)} {unite}{'s' * (reste > 1)}"
    return ", ".join(f"« {e} »" for e in vus[:3]) + (suite if reste > 0 else "")


def _lieu(article: str | None) -> str:
    return f"Article « {article} »" if article else "Avant le premier article"


# --- The Word file -------------------------------------------------------------------

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
PIC = "{http://schemas.openxmlformats.org/drawingml/2006/picture}"
# Styles of the template (modele.md), compared case-insensitively.
STYLES_MODELE = {
    "encadré", "légende", "références", "catégorie rouge", "catégorie verte",
    "catégorie bleue", "catégorie jaune", "éditorial", "source", "chiffre clé",
}  # fmt: skip
# A paragraph style "Bloc <titre>" is a type of block: the template's, or one an author
# created in Word (word-vers-vigiking.lua makes it a titled box). Never flagged.
PREFIXES_BLOCS = ("bloc ", "bloc:", "bloc-")
CARACTERES_MODELE = {
    "contre-indication",
    "crediblemeds",
    "intertitre en ligne",
    "hyperlink",
    "lien hypertexte",
}
# Word and pandoc styles that keep their meaning, or that are plain text anyway.
STYLES_CONNUS = STYLES_MODELE | {
    "normal", "normal (web)", "first paragraph", "compact", "title", "titre", "subtitle",
    "sous-titre", "author", "date", "abstract", "abstract title", "bibliography",
    "block text", "quote", "citation", "intense quote", "no spacing", "sans interligne",
    "figure", "captioned figure", "toc heading", "source code", "header", "footer",
    "en-tête", "pied de page", "annotation text", "plain text", "definition",
    "definition term", "default",
}  # fmt: skip
PREFIXES_CONNUS = PREFIXES_BLOCS + (
    "list", "liste", "paragraphe de liste", "toc ", "heading ", "titre ", "body text",
    "corps de texte", "caption", "légende", "image caption", "table caption",
    "footnote", "note de bas", "endnote", "note de fin",
)  # fmt: skip
TITRES_1 = {"heading 1", "titre 1"}
SOUS_TITRES = {"subtitle", "sous-titre"}
SANS_COULEUR = {"", "auto", "000000", "none", "ffffff"}
STYLES_SIGNALES_MAX = 5


def _noms_styles(paquet: zipfile.ZipFile) -> dict[str, str]:
    """Style id -> style name, from word/styles.xml."""
    if "word/styles.xml" not in paquet.namelist():
        return {}
    noms = {}
    for style in ET.fromstring(paquet.read("word/styles.xml")).iter(f"{W}style"):
        nom = style.find(f"{W}name")
        if nom is not None:
            noms[style.get(f"{W}styleId", "")] = nom.get(f"{W}val", "")
    return noms


def _contenu(el: ET.Element, lien: bool = False) -> Iterator[tuple[ET.Element, bool]]:
    """A paragraph's own elements (not those of a nested text box), and if in a link."""
    for enfant in el:
        if enfant.tag != f"{W}p":
            dans_lien = lien or enfant.tag == f"{W}hyperlink"
            yield enfant, dans_lien
            yield from _contenu(enfant, dans_lien)


def _texte(run: ET.Element) -> str:
    return "".join(t.text or "" for t in run.findall(f"{W}t"))


def _val(proprietes: ET.Element | None, balise: str, attribut: str = "val") -> str:
    el = proprietes.find(f"{W}{balise}") if proprietes is not None else None
    return el.get(f"{W}{attribut}", "") if el is not None else ""


def _colore(run: ET.Element, noms: dict[str, str]) -> bool:
    """Colour put by hand on a run that carries no character style of the template."""
    rpr = run.find(f"{W}rPr")
    style = _val(rpr, "rStyle")
    if noms.get(style, style).casefold() in CARACTERES_MODELE:
        return False
    proprietes = (("color", "val"), ("highlight", "val"), ("shd", "fill"))
    return any(_val(rpr, b, a).casefold() not in SANS_COULEUR for b, a in proprietes)


def _passages_colores(elements: list, noms: dict[str, str]) -> list[str]:
    """Coloured stretches of a paragraph: consecutive coloured runs make one passage."""
    passages, courant = [], ""
    for el, lien in elements:
        if el.tag != f"{W}r" or lien:
            continue
        if _colore(el, noms):
            courant += _texte(el)
        elif _texte(el).strip():
            passages, courant = [*passages, courant], ""
    return [_extrait(p) for p in [*passages, courant] if p.strip()]


def _sans_alt(elements: list) -> int:
    """Pictures with no alternative text (those marked decorative excepted)."""
    n = 0
    for el, _ in elements:
        doc_pr = (
            el.find(f"{WP}docPr") if el.tag in (f"{WP}inline", f"{WP}anchor") else None
        )
        if doc_pr is None or el.find(f".//{PIC}pic") is None:
            continue
        decoratif = any(
            d.tag.endswith("}decorative") and d.get("val") in ("1", "true")
            for d in doc_pr.iter()
        )
        n += not doc_pr.get("descr", "").strip() and not decoratif
    return n


def _constats(corps: ET.Element, noms: dict[str, str]) -> Iterator[tuple]:
    """(kind, article, detail) for each finding, in document order."""
    article = None
    for p in corps.iter(f"{W}p"):
        elements = list(_contenu(p))
        texte = "".join(_texte(el) for el, _ in elements if el.tag == f"{W}r")
        ppr = p.find(f"{W}pPr")
        nom = noms.get(_val(ppr, "pStyle"), _val(ppr, "pStyle"))
        cle = nom.casefold() or "normal"
        if cle in TITRES_1:
            article = _extrait(texte, 60) or "(titre vide)"
        elif cle in SOUS_TITRES and texte.strip():
            yield "sous-titre", None, None
        elif cle not in STYLES_CONNUS and not cle.startswith(PREFIXES_CONNUS):
            yield "style", article, nom
        if (
            cle not in STYLES_MODELE
            and _val(ppr, "shd", "fill").casefold() not in SANS_COULEUR
        ):
            yield "fond", article, _extrait(texte) or "(paragraphe vide)"
        for passage in _passages_colores(elements, noms):
            yield "couleur", article, passage
        for _ in range(_sans_alt(elements)):
            yield "image", article, None


def _grouper(constats: list[tuple], genre: str) -> dict[str | None, list]:
    """Details of one kind of finding, by article, in document order."""
    groupes: dict[str | None, list] = {}
    for g, article, detail in constats:
        if g == genre:
            groupes.setdefault(article, []).append(detail)
    return groupes


def _alertes_styles(constats: list[tuple]) -> list[Alerte]:
    """One alert per style unknown to the template, at most STYLES_SIGNALES_MAX."""
    premiers: dict[str, str | None] = {}
    for genre, article, nom in constats:
        if genre == "style":
            premiers.setdefault(nom, article)
    nombre = Counter(nom for g, _, nom in constats if g == "style")
    alertes = []
    for nom in list(premiers)[:STYLES_SIGNALES_MAX]:
        autres = nombre[nom] - 1
        plus = (
            f" (et {autres} autre{'s' * (autres > 1)} paragraphe{'s' * (autres > 1)})"
        )
        alertes.append(
            _alerte("verifier", "style", _lieu(premiers[nom]), nom, plus * (autres > 0))
        )
    if len(premiers) > STYLES_SIGNALES_MAX:
        alertes.append(
            _alerte("verifier", "styles", quoi=len(premiers) - STYLES_SIGNALES_MAX)
        )
    return alertes


def _alertes_docx(constats: list[tuple]) -> list[Alerte]:
    alertes = []
    if not any(genre == "sous-titre" for genre, _, _ in constats):
        alertes.append(_alerte("corriger", "sous-titre"))
    unites = {"couleur": ("corriger", "passage"), "fond": ("verifier", "paragraphe")}
    for genre, (niveau, unite) in unites.items():
        for article, details in _grouper(constats, genre).items():
            alertes.append(
                _alerte(niveau, genre, _lieu(article), _liste(details, unite))
            )
    for article, images in _grouper(constats, "image").items():
        n = len(images)
        lieu = "Couverture" if article is None and n == 1 else _lieu(article)
        quoi = "une image" if n == 1 else f"{n} images"
        quoi = "l'image" if lieu == "Couverture" else quoi
        alertes.append(
            _alerte("verifier", "image", lieu, quoi, "n'ont" if n > 1 else "n'a")
        )
    return alertes + _alertes_styles(constats)


def verifier_docx(docx: Path) -> list[Alerte]:
    """Check an issue written in Word: what the import would lose or get wrong."""
    try:
        with zipfile.ZipFile(docx) as paquet:
            noms = _noms_styles(paquet)
            document = ET.fromstring(paquet.read("word/document.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as erreur:
        raise SystemExit(
            f"verifier : {docx} n'est pas un fichier Word (.docx) lisible ({erreur})."
        ) from erreur
    corps = document.find(f"{W}body")
    return _alertes_docx(list(_constats(document if corps is None else corps, noms)))


# --- The imported issue --------------------------------------------------------------

ARTICLE = re.compile(r"^## +(.+?)[ \t]*(?:\{([^}\n]*)\})?[ \t]*$", re.MULTILINE)
IMAGE = re.compile(
    r"!\[((?:[^\[\]]|\[[^\]]*\])*)\]\((?:<([^>]+)>|([^)\s]+))(?:\s+\"[^\"]*\")?\)(\{[^}]*\})?"
)
A_COMPLETER = re.compile(r"\\?\[[àÀ] compléter[^\]\n]*?\\?\]", re.IGNORECASE)
SANS_AUTEUR = {"", "[auteur]", r"\[auteur\]"}
# The template's own placeholders, left in by mistake.
AUTEURS_MODELE = {"initiale. nom", "a. nom", "b. nom", "initiale nom", "prénom nom"}
RUBRIQUES = ("Cas d'ici et d'ailleurs", "Littérature", "Infos des Autorités de Santé")
# Lines meant to sit right under an article's title, found in its text instead.
LIGNE_EGAREE = re.compile(
    r"(?im)^(?:\*\*)?((?:auteurs?|rubrique|relecture|relu par)\s*:\s*[^\n]{1,80})$"
)
FORMATS_ILLISIBLES = {".emf", ".wmf", ".tif", ".tiff"}  # neither Typst nor browsers
LARGEUR_MIN = 800  # pixels


def _entete(texte: str) -> tuple[dict[str, str], str, str]:
    """Top-level front-matter keys (as plain strings), the front matter, and the body."""
    m = re.match(
        r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)", texte, re.DOTALL
    )
    if not m:
        return {}, "", texte
    cles = re.findall(r"^([\w-]+):[ \t]*(.*)$", m.group(1), re.MULTILINE)
    return (
        {cle: valeur.strip().strip("\"'") for cle, valeur in cles},
        m.group(1),
        m.group(2),
    )


def _largeur(chemin: Path) -> int | None:
    """Pixel width from a PNG, GIF or JPEG header; None for other formats."""
    with chemin.open("rb") as f:
        data = f.read(1 << 18)
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return struct.unpack(">I", data[16:20])[0]
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<H", data[6:8])[0]
    i = 2 if data[:2] == b"\xff\xd8" else len(data)
    while i + 9 <= len(data) and data[i] == 0xFF:
        marqueur = data[i + 1]
        if 0xC0 <= marqueur <= 0xCF and marqueur not in (0xC4, 0xC8, 0xCC):
            return struct.unpack(">H", data[i + 7 : i + 9])[0]  # start of frame
        i += 2 + struct.unpack(">H", data[i + 2 : i + 4])[0]
    return None


def _fichier_image(dossier: Path, chemin: str, lieu: str, nom: str) -> list[Alerte]:
    """A picture's file: missing, in a format that won't show, or too small."""
    fichier = dossier / chemin
    if re.match(r"https?://", chemin):
        return []
    if not fichier.is_file():
        return [_alerte("corriger", "introuvable", lieu, nom, chemin)]
    if fichier.suffix.lower() in FORMATS_ILLISIBLES:
        return [_alerte("corriger", "format", lieu, nom, fichier.suffix[1:].upper())]
    largeur = _largeur(fichier)
    if largeur is not None and largeur < LARGEUR_MIN:
        pixels = f"{largeur} pixel{'s' * (largeur > 1)}"
        return [_alerte("verifier", "petite", lieu, nom, pixels)]
    return []


def _images(
    dossier: Path, segment: str, lieu: str, avec_alt: bool = True
) -> list[Alerte]:
    """Pictures of one article: their file, and their text for screen readers.

    A picture alone in its paragraph is a figure: its brackets hold the caption, its
    alternative text is fig-alt. Elsewhere in a line, the brackets hold the alt text.
    """
    alertes = []
    for k, m in enumerate(IMAGE.finditer(segment), start=1):
        legende, chemin = m.group(1).strip(), m.group(2) or m.group(3)
        nom = (
            f"l'image « {_extrait(legende)} »"
            if legende
            else f"l'image n° {k} (sans légende)"
        )
        debut, fin = segment.rfind("\n", 0, m.start()) + 1, segment.find("\n", m.end())
        if segment[debut : fin if fin >= 0 else None].strip() == m.group(0):
            alt = re.search(r'fig-alt="([^"]*)"', m.group(4) or "")
            legende = alt.group(1).strip() if alt else ""
        if avec_alt and not legende:
            alertes.append(_alerte("verifier", "image", lieu, nom, "n'a"))
        alertes += _fichier_image(dossier, chemin, lieu, nom)
    return alertes


def _articles(corps: str) -> Iterator[tuple[str | None, str, str]]:
    """(title, heading attributes, text) of each article; first the text before them."""
    titres = list(ARTICLE.finditer(corps))
    yield None, "", corps[: titres[0].start() if titres else len(corps)]
    for i, m in enumerate(titres):
        fin = titres[i + 1].start() if i + 1 < len(titres) else len(corps)
        yield (
            _extrait(re.sub(r"[\\*]", "", m.group(1)), 60),
            m.group(2) or "",
            corps[m.end() : fin],
        )


def _a_completer(texte: str, lieu: str) -> list[Alerte]:
    restes = [m.group(0).replace("\\", "") for m in A_COMPLETER.finditer(texte)]
    return (
        [_alerte("corriger", "a completer", lieu, _liste(restes, "mention"))]
        if restes
        else []
    )


def _signature(lieu: str, attributs: str, texte: str) -> list[Alerte]:
    """The lines under the title: author (missing or the template's), lines left in the
    text, rubric outside the usual three."""
    auteur = re.search(r'\bauteur\s*=\s*"([^"]*)"', attributs)
    nom = auteur.group(1).strip() if auteur else ""
    alertes = []
    if nom in SANS_AUTEUR:
        alertes.append(_alerte("verifier", "auteur", lieu))
    elif nom.casefold() in AUTEURS_MODELE:
        alertes.append(_alerte("corriger", "auteur modele", lieu, nom))
    for m in LIGNE_EGAREE.finditer(texte):
        alertes.append(_alerte("verifier", "ligne egaree", lieu, _extrait(m.group(1))))
    rubrique = re.search(r'\brubrique\s*=\s*"([^"]*)"', attributs)
    if rubrique and rubrique.group(1).strip() not in RUBRIQUES:
        alertes.append(_alerte("verifier", "rubrique", lieu, rubrique.group(1).strip()))
    return alertes


def _article(
    dossier: Path, titre: str | None, attributs: str, texte: str, avec_alt: bool = True
) -> list[Alerte]:
    lieu = _lieu(titre)
    alertes = _a_completer(texte, lieu)
    hors_article = titre is None or re.search(
        r"(^|\s)\.(dos|references-page)\b", attributs
    )
    if not hors_article:
        alertes = _signature(lieu, attributs, texte) + alertes
    return alertes + _images(dossier, texte, lieu, avec_alt)


def _couverture(dossier: Path, entete: dict[str, str]) -> list[Alerte]:
    if not entete.get("couverture"):
        return [_alerte("info", "sans couverture")]
    alertes = (
        []
        if entete.get("couverture-alt")
        else [_alerte("verifier", "image", "Couverture", "l'image", "n'a")]
    )
    return alertes + _fichier_image(
        dossier, entete["couverture"], "Couverture", "l'image"
    )


def verifier_numero(qmd: Path, textes_alternatifs: bool = True) -> list[Alerte]:
    """Check an imported issue: authors, text left to fill in, pictures, cover.

    textes_alternatifs=False when the Word file was checked already: verifier_docx reports
    missing alternative texts there, in the author's terms."""
    if not qmd.is_file():
        raise SystemExit(f"verifier : fichier introuvable : {qmd}")
    entete, brut, corps = _entete(qmd.read_text(encoding="utf-8"))
    alertes = _a_completer(brut, "Titre ou sous-titre du numéro")
    for titre, attributs, texte in _articles(corps):
        alertes += _article(qmd.parent, titre, attributs, texte, textes_alternatifs)
    return alertes + _couverture(qmd.parent, entete)


# --- Page measures from the PDF template ---------------------------------------------


def verifier_mesures(mesures: list[dict]) -> list[Alerte]:
    """Articles too long for their page, or set in small print (12 pt or less) to fit."""
    alertes = []
    for mesure in mesures:
        page = f" (page {mesure['page']})" if mesure.get("page") is not None else ""
        lieu = f"Article « {mesure.get('titre') or 'sans titre'} »{page}"
        taille = float(mesure.get("taille") or 0)
        if mesure.get("deborde"):
            alertes.append(_alerte("corriger", "deborde", lieu))
        elif 0 < taille <= 12:
            pt = f"{taille:.1f}".removesuffix(".0").replace(".", ",")
            alertes.append(_alerte("verifier", "petit texte", lieu, pt))
    return alertes


# --- Links ---------------------------------------------------------------------------

URL = re.compile(r"https?://[^\s<>\"'`\]{}]+")
FIN_URL = ".,;:!?»«'\"*_"
AGENT = "vigiking-bulletin/1.0"


def _sans_fin(url: str) -> str:
    """Strip trailing punctuation, and closing brackets that the address did not open."""
    while url and (
        url[-1] in FIN_URL or (url[-1] == ")" and url.count("(") < url.count(")"))
    ):
        url = url[:-1]
    return url


def liens(texte: str) -> list[str]:
    """The http(s) addresses of a Markdown text, once each, in order."""
    sans_echappement = (
        re.sub(r"\\(?=[!-/:-@\[-`{-~])", "", m.group(0)) for m in URL.finditer(texte)
    )
    urls = (_sans_fin(url) for url in sans_echappement)
    return list(dict.fromkeys(u for u in urls if re.match(r"https?://[^/\s]", u)))


def _chercher(url: str, delai: float = 8) -> int:
    """HTTP status of url: HEAD, then GET when HEAD is refused. Raises on network errors."""
    if not re.match(r"https?://", url):
        raise ValueError(f"adresse non web : {url}")
    statut = 0
    for methode in ("HEAD", "GET"):
        requete = urllib.request.Request(
            url, method=methode, headers={"User-Agent": AGENT}
        )
        try:
            with urllib.request.urlopen(requete, timeout=delai) as reponse:
                return reponse.status
        except urllib.error.HTTPError as erreur:
            statut = erreur.code
    return statut


def _essayer(chercher: Callable[[str], int], url: str) -> tuple:
    """(url, status or None, error or None): every failure is reported, none raised."""
    try:
        return url, chercher(url), None
    except Exception as erreur:  # noqa: BLE001
        return url, None, erreur


def _alerte_lien(
    url: str, statut: int | None, erreur: Exception | None
) -> Alerte | None:
    cause = getattr(erreur, "reason", None) or erreur
    if statut is not None and statut < 400:
        return None
    if statut in (404, 410):
        return _alerte(
            "corriger", "lien mort", url, f"page introuvable, erreur {statut}"
        )
    if isinstance(cause, socket.gaierror):
        return _alerte("corriger", "lien mort", url, "site introuvable")
    if isinstance(cause, TimeoutError):
        return _alerte("verifier", "lien", url, "le site n'a pas répondu à temps")
    if statut is not None:
        return _alerte(
            "verifier",
            "lien",
            url,
            f"le site refuse la vérification automatique, code {statut}",
        )
    return _alerte("verifier", "lien", url, "le site n'a pas pu être joint")


def verifier_liens(
    urls: list[str], chercher: Callable[[str], int] | None = None, delai: float = 8
) -> list[Alerte]:
    """Dead links (corriger), links the site would not let us check (verifier).

    When no address answered at all and every failure is a network error, the computer
    is taken to be offline: one "info" instead of a list of dead links.
    """
    if not urls:
        return []
    chercher = chercher or partial(_chercher, delai=delai)
    with ThreadPoolExecutor(max_workers=min(8, len(urls))) as groupe:
        resultats = list(groupe.map(partial(_essayer, chercher), urls))
    if all(
        statut is None and isinstance(erreur, OSError)
        for _, statut, erreur in resultats
    ):
        return [_alerte("info", "hors ligne")]
    return [a for a in (_alerte_lien(*r) for r in resultats) if a is not None]


# --- Report --------------------------------------------------------------------------


def rapport(alertes: list[Alerte], titre: str) -> str:
    """Plain text: the title, then the alerts by section (to fix, to check, for info)."""
    lignes = [titre, ""]
    if not alertes:
        return "\n".join([*lignes, "✔ Rien à signaler : le bulletin est prêt."]) + "\n"
    if all(a.niveau == "info" for a in alertes):
        lignes += ["✔ Rien à corriger ni à vérifier.", ""]
    for niveau, (entete, signe) in SECTIONS.items():
        du_niveau = [f"{signe} {a.message}" for a in alertes if a.niveau == niveau]
        if du_niveau:
            lignes += [f"{entete} ({len(du_niveau)})", *du_niveau, ""]
    return "\n".join(lignes).rstrip() + "\n"
