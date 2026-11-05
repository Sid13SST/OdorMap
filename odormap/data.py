"""Dataset loading and validation.

The training table is data/leffingwell.csv, built by scripts/fetch_data.py by
joining the pyrfume Leffingwell molecules.csv and behavior.csv on CID. Every
column that is not a molecule-metadata column is a binary 0/1 odor label.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "leffingwell.csv"
SMILES_COL = "IsomericSMILES"
ID_COL = "CID"
NAME_COL = "name"
META_COLS = (ID_COL, "MolecularWeight", SMILES_COL, "IUPACName", NAME_COL)


def load_dataset(path: Path | str = DATA_PATH) -> tuple[pd.DataFrame, list[str]]:
    """Return (dataframe, label_columns). Raises if the file is missing."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python scripts/fetch_data.py` first."
        )
    df = pd.read_csv(path)
    validate_dataframe(df)
    labels = label_columns(df)
    return df, labels


def label_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in META_COLS]


def validate_dataframe(df: pd.DataFrame) -> None:
    """Basic schema checks. Raises ValueError on problems."""
    if SMILES_COL not in df.columns:
        raise ValueError(f"missing required column {SMILES_COL!r}")
    labels = label_columns(df)
    if not labels:
        raise ValueError("no label columns found")
    if df[SMILES_COL].isna().any():
        raise ValueError("null SMILES present")
    vals = df[labels].to_numpy()
    if not np.isin(vals, (0, 1)).all():
        raise ValueError("label columns must be binary 0/1")
