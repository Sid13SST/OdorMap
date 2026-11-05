"""Download the Leffingwell odor dataset (pyrfume mirror) into data/leffingwell.csv.

Fetches molecules.csv and behavior.csv from pyrfume-data, joins them on
Stimulus = CID, and saves the merged training table (SMILES column:
IsomericSMILES). Licensed CC-BY-NC 4.0; see DATA.md for source and attribution.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odormap.data import DATA_PATH  # noqa: E402
from odormap.fetch import BEHAVIOR_URL, MOLECULES_URL, fetch  # noqa: E402,F401  (re-exported)

DEFAULT_OUT = DATA_PATH


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    fetch(args.out, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
