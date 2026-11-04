"""Inference helpers shared by scripts/predict.py and app.py.

The saved model (models/baseline_lr.joblib) is refit on *all* dataset
molecules, so a prediction for a molecule that is in the dataset is a
training-set prediction (the model may simply have memorized its labels).
Every prediction therefore carries a training-membership flag, computed by
exact match on canonical, stereo-free SMILES.

Outputs are per-label logistic-regression *scores* (model confidence), not
calibrated probabilities; see results/calibration.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
from rdkit import Chem

from .data import REPO_ROOT, SMILES_COL, load_dataset
from .features import mol_from_smiles, morgan_fp

MODEL_PATH = REPO_ROOT / "models" / "baseline_lr.joblib"

IN_TRAINING = "in training data (memorization possible)"
NEW_MOLECULE = "new molecule (true generalization)"


def membership_key(smiles: str) -> str | None:
    """Canonical SMILES with stereochemistry removed (the dataset's
    `nonStereoSMILES` has no stereo). None if unparseable."""
    mol = mol_from_smiles(smiles)
    return None if mol is None else Chem.MolToSmiles(mol, isomericSmiles=False)


def membership_keys(smiles_list: Iterable[str]) -> frozenset[str]:
    keys = {membership_key(s) for s in smiles_list}
    keys.discard(None)
    return frozenset(keys)


@dataclass(frozen=True)
class Prediction:
    smiles: str
    canonical: str
    in_training: bool
    scores: list[tuple[str, float]]  # (label, score), descending

    @property
    def membership(self) -> str:
        return IN_TRAINING if self.in_training else NEW_MOLECULE


class Predictor:
    def __init__(self, model, labels: list[str], training_keys: frozenset[str]):
        self.model = model
        self.labels = list(labels)
        self.training_keys = frozenset(training_keys)

    @classmethod
    def load(cls, model_path: Path | str = MODEL_PATH) -> "Predictor":
        bundle = joblib.load(model_path)
        keys = bundle.get("training_keys")
        if keys is None:  # bundles saved before the membership flag existed
            df, _ = load_dataset()
            keys = membership_keys(df[SMILES_COL])
        return cls(bundle["model"], bundle["labels"], frozenset(keys))

    def is_in_training(self, smiles: str) -> bool:
        key = membership_key(smiles)
        return key is not None and key in self.training_keys

    def predict(self, smiles: str, top: int = 10) -> Prediction:
        """Raises ValueError for invalid SMILES."""
        x = morgan_fp(smiles)[None, :]
        s = self.model.predict_proba(x)[0]
        order = np.argsort(-s)[:top]
        return Prediction(
            smiles=smiles,
            canonical=membership_key(smiles),
            in_training=self.is_in_training(smiles),
            scores=[(self.labels[j], float(s[j])) for j in order],
        )
