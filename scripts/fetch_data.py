"""Download the GoodScents + Leffingwell merged odor dataset into data/.

Source: OpenPOM replication (MIT license). See DATA.md for provenance and
the open licensing question about the original catalogs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

URL = (
    "https://raw.githubusercontent.com/ARY2260/openpom/main/openpom/data/"
    "curated_datasets/curated_GS_LF_merged_4983.csv"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "curated_GS_LF_merged_4983.csv"


def fetch(out: Path = DEFAULT_OUT, force: bool = False) -> Path:
    if out.exists() and not force:
        print(f"Already present: {out} (use --force to re-download)")
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {URL}")
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    text = resp.text
    if not text.lower().startswith("nonstereosmiles"):
        raise RuntimeError("Unexpected file header; refusing to save.")
    out.write_text(text, encoding="utf-8")
    n_rows = text.count("\n") - 1
    print(f"Saved {out} ({len(text):,} bytes, ~{n_rows:,} data rows)")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    fetch(args.out, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
