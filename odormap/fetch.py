"""Download the Leffingwell odor dataset (pyrfume mirror) and build the training table.

Shared by scripts/fetch_data.py and the app's first-run setup. Two CSVs are
fetched from the pyrfume-data repository and joined on Stimulus = CID:

- molecules.csv: CID, MolecularWeight, IsomericSMILES, IUPACName, name
- behavior.csv:  Stimulus + one binary 0/1 column per odor descriptor

The joined table is saved to data/leffingwell.csv (git-ignored). The label
values are not modified. The dataset is licensed CC-BY-NC 4.0; see DATA.md.
"""
from __future__ import annotations

import io
import time
from pathlib import Path

import pandas as pd
import requests

from .data import DATA_PATH

BASE = "https://raw.githubusercontent.com/pyrfume/pyrfume-data/main/leffingwell/"
MOLECULES_URL = BASE + "molecules.csv"
BEHAVIOR_URL = BASE + "behavior.csv"
URLS = (MOLECULES_URL, BEHAVIOR_URL)
ATTEMPTS = 3


class FetchError(RuntimeError):
    """The dataset could not be downloaded (network error or unexpected content)."""


def _download(url: str, timeout: float) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _get(url: str, header: str, timeout: float, attempts: int) -> str:
    """Download `url` with retries; check that the first line starts with `header`."""
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
    if not text.startswith(header):
        raise FetchError(f"Unexpected file header from {url}; refusing to save.")
    return text


def join_tables(molecules: pd.DataFrame, behavior: pd.DataFrame) -> pd.DataFrame:
    """Join molecules and labels on Stimulus = CID (1:1; raises FetchError otherwise)."""
    if not molecules["CID"].is_unique or not behavior["Stimulus"].is_unique:
        raise FetchError("Duplicate CID / Stimulus keys in the downloaded tables.")
    if set(molecules["CID"]) != set(behavior["Stimulus"]):
        raise FetchError("molecules.csv CIDs and behavior.csv Stimulus IDs do not match.")
    merged = molecules.merge(behavior, left_on="CID", right_on="Stimulus", how="inner",
                             validate="one_to_one")
    return merged.drop(columns="Stimulus")


def fetch(out: Path = DATA_PATH, force: bool = False, timeout: float = 60,
          attempts: int = ATTEMPTS) -> Path:
    """Download both CSVs, join them, and save the table to `out`.

    Skipped if `out` exists and not `force`. Retries transient network errors;
    raises FetchError with a readable message if every attempt fails or the
    content is not the expected CSV.
    """
    out = Path(out)
    if out.exists() and not force:
        print(f"Already present: {out} (use --force to re-download)")
        return out
    mol_text = _get(MOLECULES_URL, "CID,", timeout, attempts)
    beh_text = _get(BEHAVIOR_URL, "Stimulus,", timeout, attempts)
    behavior = pd.read_csv(io.StringIO(beh_text))
    merged = join_tables(pd.read_csv(io.StringIO(mol_text)), behavior)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".part")
    merged.to_csv(tmp, index=False)
    tmp.replace(out)  # never leave a half-written CSV behind
    print(f"Saved {out} ({len(merged):,} molecules, "
          f"{behavior.shape[1] - 1} label columns)")
    return out
