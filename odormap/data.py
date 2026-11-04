"""Dataset loading and validation."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "curated_GS_LF_merged_4983.csv"
SMILES_COL = "nonStereoSMILES"
DESC_COL = "descriptors"


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
    return [c for c in df.columns if c not in (SMILES_COL, DESC_COL)]


def validate_dataframe(df: pd.DataFrame) -> None:
    """Basic schema checks. Raises ValueError on problems."""
    for col in (SMILES_COL, DESC_COL):
        if col not in df.columns:
            raise ValueError(f"missing required column {col!r}")
    labels = label_columns(df)
    if not labels:
        raise ValueError("no label columns found")
    if df[SMILES_COL].isna().any():
        raise ValueError("null SMILES present")
    vals = df[labels].to_numpy()
    if not np.isin(vals, (0, 1)).all():
        raise ValueError("label columns must be binary 0/1")
