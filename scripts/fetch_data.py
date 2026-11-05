"""Download the GoodScents + Leffingwell merged odor dataset into data/.

Source: OpenPOM replication (MIT license for its code). See DATA.md for
provenance and the unresolved redistribution terms of the underlying data.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odormap.data import DATA_PATH  # noqa: E402
from odormap.fetch import URL, fetch  # noqa: E402,F401  (URL re-exported)

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
