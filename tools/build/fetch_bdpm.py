"""Download the open files of the public medicines database (BDPM, ANSM) used by
tools/build/make_bdpm_liens.py: products and their marketing status, compositions,
generic groups, and the download page (for the files' update date).

Writes them to data/bdpm/ (a local cache, not committed: about 7 MB). The BDPM is
updated every month; run this, then make_bdpm_liens.py, at each update.
Licence Ouverte (Etalab): cite the source and the date of its last update.

Usage: python tools/build/fetch_bdpm.py
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "bdpm"
BASE = "https://base-donnees-publique.medicaments.gouv.fr"
FILES = ("CIS_bdpm.txt", "CIS_COMPO_bdpm.txt", "CIS_GENER_bdpm.txt")
PAGE = "telechargement.html"
MIN_BYTES = 100_000  # each file is over 1 MB: a smaller one is an error page


def _get(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "pharmacovigilance-normandie-build"}
    )
    # Only fixed https addresses on the BDPM site are opened.
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        content = _get(f"{BASE}/download/file/{name}")
        if len(content) < MIN_BYTES:
            raise SystemExit(f"fetch_bdpm : {name} ne fait que {len(content)} octets.")
        (CACHE / name).write_bytes(content)
        print(f"data/bdpm/{name} : {len(content) // 1024} Ko")
    (CACHE / PAGE).write_bytes(_get(f"{BASE}/telechargement"))
    print(f"data/bdpm/{PAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
