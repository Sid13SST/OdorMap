"""Download the GoodScents + Leffingwell merged odor dataset.

Shared by scripts/fetch_data.py and the app's first-run setup. The file is
fetched at runtime from the OpenPOM repository and never committed; see
DATA.md for provenance and the unresolved redistribution terms.
"""
from __future__ import annotations

import time
from pathlib import Path

import requests

from .data import DATA_PATH

URL = (
    "https://raw.githubusercontent.com/ARY2260/openpom/main/openpom/data/"
    "curated_datasets/curated_GS_LF_merged_4983.csv"
)
ATTEMPTS = 3


class FetchError(RuntimeError):
    """The dataset could not be downloaded (network error or unexpected content)."""


def _download(url: str, timeout: float) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch(out: Path = DATA_PATH, force: bool = False, url: str = URL,
          timeout: float = 60, attempts: int = ATTEMPTS) -> Path:
    """Download the CSV to `out` (skipped if present and not `force`).

    Retries transient network errors; raises FetchError with a readable
    message if every attempt fails or the content is not the expected CSV.
    """
    out = Path(out)
    if out.exists() and not force:
        print(f"Already present: {out} (use --force to re-download)")
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    last = None
    for i in range(attempts):
        try:
            text = _download(url, timeout)
            break
        except requests.RequestException as e:
            last = e
            if i < attempts - 1:
                time.sleep(2 ** (i + 1))
    else:
        raise FetchError(f"Could not download the dataset from {url} after "
                         f"{attempts} attempts ({type(last).__name__}: {last}).") from last
    if not text.lower().startswith("nonstereosmiles"):
        raise FetchError(f"Unexpected file header from {url}; refusing to save.")
    tmp = out.with_suffix(out.suffix + ".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(out)  # never leave a half-written CSV behind
    n_rows = text.count("\n") - 1
    print(f"Saved {out} ({len(text):,} bytes, ~{n_rows:,} data rows)")
    return out
