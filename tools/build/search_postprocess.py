"""Make the site search forgiving: accent-free text and common synonyms.

Quarto's search (Fuse.js, strict threshold) misses "paracetamol" typed without its
accent, or "newsletter" for Vigiking: the user panel hit both (docs/panel/). After
each render, this script adds to every entry of _site/search.json an accent-free copy
of its text and the synonyms of the words it contains. The original text stays first,
so the snippets shown to the reader do not change.

Run by Quarto as a post-render script (see _quarto.yml), or by hand:
    python tools/build/search_postprocess.py [path/to/search.json]
"""

from __future__ import annotations

import json
import os
import sys
import unicodedata
from pathlib import Path

MARKER = " ⁂ "  # separates the original text from what this script adds

# accent-free trigger found in an entry -> words people type for it
SYNONYMS: dict[str, str] = {
    "pseudoephedrine": "decongestionnant decongestionnants nez bouche",
    "vigiking": "newsletter bulletin lettre abonnement abonner",
    "ecraser": "broyer piler pilon",
    "deglutition": "avaler fausse route",
    "ciprofloxacine": "cipro ciflox siprofloxacine ciprofloxacin",
    "fluoroquinolone": "antibiotique cipro",
    "paracetamol": "doliprane dafalgan efferalgan",
    "ibuprofene": "advil nurofen",
    "apixaban": "eliquis",
    "rivaroxaban": "xarelto",
    "effet indesirable": "effet secondaire effets secondaires",
    "tendon": "tendinite talon achille",
    "stage": "stages internat externat",
    "declarer": "signaler signalement",
    "intoxication": "empoisonnement avale poison poisoning",
    "allaitement": "allaiter lactation",
    "grossesse": "enceinte",
    "estroprogestatif": "pilule contraceptif contraception",
    "levofloxacine": "tavanic",
    "toux": "cough",
    "hypertension": "tension blood pressure",
    "frequence indeterminee": "frequences frequence",
}


def fold(text: str) -> str:
    """Lower case, without diacritics."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def enrich(entry: dict) -> dict:
    """Return a copy of a search entry whose text also holds its folded form and synonyms."""
    text = entry.get("text", "") or ""
    original = text.split(MARKER, 1)[0]
    folded = fold(original + " " + entry.get("title", ""))
    extra = [folded] if folded.strip() else []
    extra += [words for trigger, words in SYNONYMS.items() if trigger in folded]
    return {**entry, "text": original + (MARKER + " ".join(extra) if extra else "")}


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        path = Path(argv[1])
    else:
        output_dir = os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site")
        path = Path(output_dir) / "search.json"
    if not path.exists():
        print(f"search_postprocess: {path} absent, rien à faire.")
        return 0
    entries = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        json.dumps([enrich(e) for e in entries], ensure_ascii=False), encoding="utf-8"
    )
    print(f"search_postprocess: {len(entries)} entrées enrichies dans {path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
