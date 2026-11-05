"""Train the final baseline model and save it as models/baseline_lr.joblib.

Single code path shared by scripts/run_baseline.py and app.py, so the saved
bundle schema is the same however the model was produced:

    {"model", "labels", "radius", "n_bits", "training_keys"}

`ensure_model` is the app's first-run hook: if the model file is missing it
fetches the dataset (if needed) and trains the model, so the app works on a
fresh clone without the dataset or model committed (see DATA.md).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import joblib
import numpy as np

from .data import DATA_PATH, SMILES_COL, load_dataset
from .features import N_BITS, RADIUS, featurize
from .fetch import fetch
from .inference import MODEL_PATH, membership_keys
from .model import build_model


def fit_bundle(X: np.ndarray, Y: np.ndarray, labels: Sequence[str],
               smiles: Sequence[str], n_jobs: int = -1) -> dict:
    """Fit the baseline on all of (X, Y) and return the saveable bundle."""
    model = build_model(n_jobs=n_jobs)
    model.fit(X, Y)
    return {"model": model, "labels": list(labels), "radius": RADIUS, "n_bits": N_BITS,
            "training_keys": membership_keys(smiles)}


def save_bundle(bundle: dict, path: Path | str = MODEL_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    joblib.dump(bundle, tmp)
    tmp.replace(path)  # a crash mid-write never leaves a truncated model
    return path


def train_and_save(data_path: Path | str = DATA_PATH,
                   model_path: Path | str = MODEL_PATH) -> Path:
    """Load the dataset, fit the final model on all molecules, save it."""
    df, labels = load_dataset(data_path)
    smiles = df[SMILES_COL].tolist()
    bundle = fit_bundle(featurize(smiles), df[labels].to_numpy(), labels, smiles)
    return save_bundle(bundle, model_path)


def ensure_model(model_path: Path | str = MODEL_PATH,
                 data_path: Path | str = DATA_PATH) -> Path:
    """Return model_path, fetching the data and training first if it is missing.

    Raises odormap.fetch.FetchError if the dataset cannot be downloaded.
    """
    model_path, data_path = Path(model_path), Path(data_path)
    if model_path.exists():
        return model_path
    if not data_path.exists():
        fetch(data_path)
    return train_and_save(data_path, model_path)
