"""Predict odor descriptors for a single molecule from its SMILES string.

Usage: python scripts/predict.py "COc1cc(C=O)ccc1O" [--top 10]

Requires models/baseline_lr.joblib (create with scripts/run_baseline.py).
Predicts catalog-style odor descriptors of a single pure molecule; this is
not a model of real-world odor sensing, mixtures, or concentration effects.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odormap.data import REPO_ROOT  # noqa: E402
from odormap.features import morgan_fp  # noqa: E402

MODEL_PATH = REPO_ROOT / "models" / "baseline_lr.joblib"


def predict(smiles: str, top: int = 10, model_path: Path = MODEL_PATH):
    bundle = joblib.load(model_path)
    x = morgan_fp(smiles)[None, :]
    probs = bundle["model"].predict_proba(x)[0]
    order = np.argsort(-probs)[:top]
    return [(bundle["labels"][j], float(probs[j])) for j in order]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("smiles")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--model", type=Path, default=MODEL_PATH)
    args = p.parse_args(argv)
    if not args.model.exists():
        print(f"Model not found at {args.model}. Run scripts/run_baseline.py first.",
              file=sys.stderr)
        return 2
    try:
        preds = predict(args.smiles, args.top, args.model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"SMILES: {args.smiles}")
    for rank, (label, prob) in enumerate(preds, 1):
        print(f"{rank:2d}. {label:<16s} {prob:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
