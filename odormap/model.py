"""Baseline model: Morgan fingerprints + one-vs-rest logistic regression."""
from __future__ import annotations

import warnings

import numpy as np
from sklearn.exceptions import UndefinedMetricWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
from sklearn.multiclass import OneVsRestClassifier

C = 1.0  # sklearn default; fixed a priori, not tuned
MAX_ITER = 2000


def build_model(n_jobs: int = -1) -> OneVsRestClassifier:
    base = LogisticRegression(
        C=C, class_weight="balanced", solver="liblinear", max_iter=MAX_ITER
    )
    return OneVsRestClassifier(base, n_jobs=n_jobs)


def evaluate(Y_true: np.ndarray, Y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """Multi-label metrics. Labels with no positives (or no negatives) in
    Y_true are excluded from macro ROC-AUC / mAP, and the count is reported."""
    Y_true = np.asarray(Y_true)
    pos = Y_true.sum(axis=0)
    ok = (pos > 0) & (pos < len(Y_true))
    Y_pred = (Y_prob >= threshold).astype(int)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UndefinedMetricWarning)
        return {
            "macro_roc_auc": roc_auc_score(Y_true[:, ok], Y_prob[:, ok], average="macro"),
            "micro_roc_auc": roc_auc_score(Y_true, Y_prob, average="micro"),
            "macro_f1@0.5": f1_score(Y_true, Y_pred, average="macro", zero_division=0),
            "mean_avg_precision": average_precision_score(
                Y_true[:, ok], Y_prob[:, ok], average="macro"
            ),
            "n_labels_scored": int(ok.sum()),
            "n_labels_skipped": int((~ok).sum()),
        }
