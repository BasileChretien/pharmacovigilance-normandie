"""Layout of figures redrawn for Dark Reader (docs/mode-sombre.md): what the redraw must
not have moved out of place."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_migraine_legend_lines_start_after_the_widened_badges():
    # The badges grew to 48 units and their labels moved to x=74; a wrapped second line
    # must move with its first (review of #43).
    svg = (ROOT / "assets" / "img" / "figures" / "migraine-1.svg").read_text(encoding="utf-8")
    starts = {
        text: float(x)
        for x, y, text in re.findall(r'<text x="([0-9.]+)" y="([0-9.]+)">([^<]+)</text>', svg)
        if 170 < float(y) < 290
    }
    assert starts and set(starts.values()) == {74.0}, starts
