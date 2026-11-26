"""Check the structure and the plain-language rules of the site's pages.

Rules come from docs/regles-redaction.md (HAS guides on written patient
information, 2008 and 2012, and FALC principles). Patient rules only read the
text inside ::: {.texte-patient} blocks.

Severity follows the page's status: on a draft (statut: brouillon) the writing
findings are warnings; on a reviewed or published page (relu, publie) the
blocking rules become errors. Front-matter problems are always errors.

Usage:
    python tools/checks/check_content.py            # every page
    python tools/checks/check_content.py page.qmd   # some pages
    python tools/checks/check_content.py --strict   # treat drafts as published
Exit code 1 if there is at least one error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
JARGON_FILE = ROOT / "data" / "jargon.yml"
EXCLUDED_DIRS = {"_site", "_templates", "docs", "node_modules", ".quarto", ".venv", "tests", "tools"}

STATUTS = {"brouillon", "relu", "publie"}
STRICT_STATUTS = {"relu", "publie"}
PAGES_QUAND_CONSULTER = ("medicaments/classes/", "medicaments/maux-courants/")
NE_PAS_ARRETER = "ne modifiez pas votre traitement"
FORMULES_CREUSES = (
    "il est important de noter",
    "il convient de noter",
    "il est essentiel de",
    "joue un rôle clé",
    "jouer un rôle clé",
    "dans un monde où",
    "n'hésitez pas à",
    "en effet,",
)
MAX_WORDS = 25
AVG_WORDS = 15
WORDS_PER_HEADING = 150
MAX_A_RETENIR = 3

_OPEN = re.compile(r"^(:{3,})\s*(\{[^}]*\}|[\w-]+)\s*$")
_CLOSE = re.compile(r"^:{3,}\s*$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCED_CODE = re.compile(r"^\s*(```|~~~).*?^\s*\1\s*$", re.DOTALL | re.MULTILINE)
_BULLET = re.compile(r"^([-*+]|\d+[.)])\s+(.*)$")
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=[«\"(A-ZÀ-ÖØ-Ý0-9])")
_WORD = re.compile(r"[\wÀ-ÿœŒ'’-]+")
_ACRONYM = re.compile(r"\b[A-ZÀ-Ý]{2,}[0-9]*\b")
_PASSIVE = re.compile(
    r"\b(est|sont|été|était|étaient|sera|seront|soit|soient)\s+(\w+(?:é|ée|és|ées))\b",
    re.IGNORECASE,
)
_PERCENT = re.compile(r"\d\s?%|\bpour\s?cent\b", re.IGNORECASE)
_VOWELS = re.compile(r"[aeiouyàâäéèêëîïôöùûüÿœæ]+", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    level: str  # "error", "warning" or "info"
    rule: str
    message: str


# --- parsing -----------------------------------------------------------------

def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split a .qmd file into its YAML front matter and its body."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            meta = yaml.safe_load("".join(lines[1:i])) or {}
            return meta, "".join(lines[i + 1 :])
    return {}, text


def extract_divs(body: str, cls: str) -> list[str]:
    """Return the inner text of each outermost fenced div carrying class `cls`."""
    lines = body.splitlines()
    found: list[str] = []
    stack: list[tuple[set[str], int]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        opening = _OPEN.match(stripped)
        if opening:
            attrs = opening.group(2)
            classes = set(re.findall(r"\.([\w-]+)", attrs)) if attrs.startswith("{") else {attrs}
            stack.append((classes, i))
            continue
        if _CLOSE.match(stripped) and stack:
            classes, start = stack.pop()
            if cls in classes and not any(cls in outer for outer, _ in stack):
                found.append("\n".join(lines[start + 1 : i]))
    return found


def clean_inline(text: str) -> str:
    """Strip inline Markdown: images, links, emphasis, code marks, spans."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\{[^}]*\}", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    """Sentences of the prose: headings, tables, comments and div fences are skipped;
    each list item counts as one sentence or more."""
    text = _FENCED_CODE.sub("", _COMMENT.sub("", text))
    sentences: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            sentences.extend(_split_paragraph(" ".join(paragraph)))
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith((":::", "#", "|")):
            flush()
            continue
        item = _BULLET.match(line)
        if item:
            flush()
            sentences.extend(_split_paragraph(clean_inline(item.group(2))))
            continue
        paragraph.append(clean_inline(line))
    flush()
    return [s for s in sentences if s]


def _split_paragraph(paragraph: str) -> list[str]:
    return [p.strip() for p in _SENTENCE_END.split(paragraph.strip()) if p.strip()]


def count_words(sentence: str) -> int:
    return sum(1 for token in _WORD.findall(sentence) if re.search(r"[\wÀ-ÿ]", token))


def _syllables(word: str) -> int:
    groups = len(_VOWELS.findall(word))
    if groups > 1 and word.lower().endswith(("e", "es", "ent")) and not word.lower().endswith(("é", "ée", "ées")):
        groups -= 1
    return max(groups, 1)


def kandel_moles(text: str) -> float:
    """Flesch reading ease adapted to French by Kandel and Moles (1958)."""
    sentences = split_sentences(text) or [text]
    words = [w for s in sentences for w in _WORD.findall(s) if re.search(r"[A-Za-zÀ-ÿ]", w)]
    if not words:
        return 0.0
    syllables = sum(_syllables(w) for w in words)
    return 207 - 1.015 * (len(words) / len(sentences)) - 73.6 * (syllables / len(words))


# --- rules -------------------------------------------------------------------

def _is_date(value) -> bool:
    if isinstance(value, (dt.date, dt.datetime)):
        return True
    return isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None


def _present(value) -> bool:
    return value not in (None, "", "null")


def front_matter_rules(meta: dict, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    # Landing pages and institutional pages (legal notice, team…) need no medical source.
    navigation = path.name == "index.qmd" or meta.get("type") in ("navigation", "institutionnel")
    for key in ("title", "description"):
        if not _present(meta.get(key)):
            findings.append(Finding("error", "FM-CHAMP", f"champ « {key} » manquant"))
    if navigation and "statut" not in meta:
        return findings
    statut = str(meta.get("statut", "")).strip()
    if statut not in STATUTS:
        findings.append(Finding("error", "FM-STATUT", f"statut « {statut} » : attendu brouillon, relu ou publie"))
    sources = meta.get("sources") or []
    valid = [s for s in sources if isinstance(s, dict) and _present(s.get("titre")) and _present(s.get("url"))]
    if not navigation and not valid:
        findings.append(Finding("error", "FM-SOURCES", "aucune source avec titre et URL"))
    for s in sources if isinstance(sources, list) else []:
        if isinstance(s, dict) and _present(s.get("consulte_le")) and not _is_date(s.get("consulte_le")):
            findings.append(Finding("error", "FM-DATE", f"date de consultation invalide : {s.get('consulte_le')}"))
    liens = meta.get("pour_aller_plus_loin") or []
    for lien in liens if isinstance(liens, list) else [liens]:
        url = str(lien.get("url") or "") if isinstance(lien, dict) else ""
        if not (isinstance(lien, dict) and _present(lien.get("titre")) and url.startswith("https://")):
            findings.append(Finding("error", "FM-LIENS", f"lien « pour aller plus loin » sans titre ou sans URL https : {lien}"))
    if statut in STRICT_STATUTS and not (_present(meta.get("relu_par")) and _present(meta.get("relu_le"))):
        findings.append(Finding("error", "FM-RELECTURE", "page relue ou publiée sans relu_par et relu_le"))
    for key in ("relu_le", "prochaine_relecture"):
        if _present(meta.get(key)) and not _is_date(meta.get(key)):
            findings.append(Finding("error", "FM-DATE", f"{key} doit être une date AAAA-MM-JJ"))
    return findings


def _first_unexplained(pattern: str, text: str) -> bool:
    """True when the first occurrence of `pattern` is neither followed by ' (' nor inside '( )'."""
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return False
    after = text[match.end() : match.end() + 2]
    before = text[max(0, match.start() - 1) : match.start()]
    return not (after.lstrip().startswith("(") or before == "(")


def patient_rules(patient: str, posix: str, level: str, jargon: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    lower = patient.lower()
    needs_boxes = any(prefix in posix for prefix in PAGES_QUAND_CONSULTER)

    boxes = extract_divs(patient, "a-retenir")
    if not boxes:
        findings.append(Finding(level, "PAT-A-RETENIR", "encadré « À retenir » manquant"))
    for box in boxes:
        points = sum(1 for line in box.splitlines() if _BULLET.match(line.strip()))
        if points > MAX_A_RETENIR:
            findings.append(Finding(level, "PAT-A-RETENIR", f"« À retenir » a {points} points (3 au plus)"))

    if needs_boxes and not extract_divs(patient, "quand-consulter"):
        findings.append(Finding(level, "PAT-QUAND-CONSULTER", "encadré « Quand consulter » manquant"))
    if needs_boxes and NE_PAS_ARRETER not in lower:
        findings.append(Finding(level, "PAT-NE-PAS-ARRETER", "phrase « Ne modifiez pas votre traitement… » absente"))

    sentences = split_sentences(patient)
    counts = [count_words(s) for s in sentences]
    for sentence, n in zip(sentences, counts):
        if n > MAX_WORDS:
            findings.append(Finding(level, "PAT-PHRASE-LONGUE", f"{n} mots : « {sentence[:90]}… »"))
    if counts and sum(counts) / len(counts) > AVG_WORDS:
        findings.append(Finding("warning", "PAT-PHRASE-MOYENNE", f"{sum(counts) / len(counts):.1f} mots par phrase en moyenne (15 visés)"))

    prose = " ".join(sentences)
    if _PERCENT.search(prose):
        findings.append(Finding("warning", "PAT-POURCENTAGE", "pourcentage dans le texte patient : écrire « 1 personne sur 100 »"))

    for term, plain in jargon.items():
        if _first_unexplained(rf"\b{re.escape(term)}s?\b", prose):
            findings.append(Finding(level, "PAT-JARGON", f"« {term} » non expliqué à sa première apparition (proposition : {plain})"))

    for acronym in dict.fromkeys(_ACRONYM.findall(prose)):
        if _first_unexplained(rf"\b{re.escape(acronym)}\b", prose):
            findings.append(Finding(level, "PAT-SIGLE", f"sigle « {acronym} » non développé à sa première apparition"))

    words_since_heading = 0
    for line in _FENCED_CODE.sub("", _COMMENT.sub("", patient)).splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            words_since_heading = 0
        elif stripped and not stripped.startswith((":::", "|")):
            words_since_heading += count_words(clean_inline(stripped))
            if words_since_heading > WORDS_PER_HEADING:
                findings.append(Finding("warning", "PAT-INTERTITRES", "plus de 150 mots sans intertitre"))
                break

    passives = _PASSIVE.findall(prose)
    if len(passives) > 2:
        findings.append(Finding("warning", "PAT-PASSIF", f"{len(passives)} tournures passives probables (voix active visée)"))

    for formule in FORMULES_CREUSES:
        if formule in lower:
            findings.append(Finding("warning", "PAT-FORMULE", f"formule à éviter : « {formule} »"))

    if sentences:
        findings.append(Finding("info", "PAT-LISIBILITE", f"indice de lisibilité (Kandel-Moles) : {kandel_moles(prose):.0f}"))
    return findings


def check_text(text: str, path: Path, jargon: dict[str, str], strict: bool = False) -> list[Finding]:
    meta, body = parse_front_matter(text)
    findings = front_matter_rules(meta, path)
    statut = str(meta.get("statut", "")).strip()
    level = "error" if (strict or statut in STRICT_STATUTS) else "warning"
    blocks = extract_divs(body, "texte-patient")
    if blocks:
        findings.extend(patient_rules("\n\n".join(blocks), path.as_posix(), level, jargon))
    return findings


# --- command line ------------------------------------------------------------

def load_jargon() -> dict[str, str]:
    if not JARGON_FILE.exists():
        return {}
    data = yaml.safe_load(JARGON_FILE.read_text(encoding="utf-8")) or {}
    return {str(k): str(v) for k, v in data.items()}


def site_pages() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.qmd")
        if not any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts)
    )


def _display(path: Path) -> str:
    """Path relative to the project when the file is inside it, else as given."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--strict", action="store_true", help="appliquer aux brouillons les règles des pages publiées")
    parser.add_argument("--quiet", action="store_true", help="n'afficher que les erreurs")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    jargon = load_jargon()
    pages = [p.resolve() for p in args.paths] or site_pages()
    totals = {"error": 0, "warning": 0}
    for page in pages:
        findings = check_text(page.read_text(encoding="utf-8"), page, jargon, strict=args.strict)
        shown = [f for f in findings if f.level == "error" or (not args.quiet and f.level != "info")]
        for f in findings:
            if f.level in totals:
                totals[f.level] += 1
        if shown:
            print(f"\n{_display(page)}")
            for f in shown:
                print(f"  [{f.level.upper():7}] {f.rule}: {f.message}")
    print(f"\n{len(pages)} pages, {totals['error']} erreurs, {totals['warning']} avertissements.")
    return 1 if totals["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
