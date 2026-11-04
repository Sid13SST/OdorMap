"""Predict odor descriptors for a single molecule from its SMILES string.

Usage: python scripts/predict.py "COc1cc(C=O)ccc1O" [--top 10]

Requires models/baseline_lr.joblib (create with scripts/run_baseline.py).
Predicts catalog-style odor descriptors of a single pure molecule; this is
not a model of real-world odor sensing, mixtures, or concentration effects.

Outputs are model confidence scores, not calibrated probabilities
(see results/calibration.md). Each prediction is flagged as either in the
training data (the saved model was fit on all dataset molecules, so
memorization is possible) or a new molecule.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odormap.inference import MODEL_PATH, Prediction, Predictor  # noqa: E402


def predict(smiles: str, top: int = 10, model_path: Path = MODEL_PATH) -> Prediction:
    return Predictor.load(model_path).predict(smiles, top)


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
        pred = predict(args.smiles, args.top, args.model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"SMILES: {args.smiles}")
    print(f"Training membership: {pred.membership}")
    print("Scores are model confidence, not calibrated probabilities.")
    for rank, (label, score) in enumerate(pred.scores, 1):
        print(f"{rank:2d}. {label:<16s} {score:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
