"""Calibration metrics: reliability bins and expected calibration error."""
from __future__ import annotations

import numpy as np


def reliability_bins(y_true, y_score, n_bins: int = 10) -> dict:
    """Equal-width bins on [0, 1]. Returns per-bin count, mean score, and
    observed positive fraction (NaN for empty bins)."""
    y = np.asarray(y_true, dtype=float).ravel()
    s = np.asarray(y_score, dtype=float).ravel()
    if y.shape != s.shape:
        raise ValueError("y_true and y_score must have the same size")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    # bin i holds edges[i] <= s < edges[i+1]; s == 1.0 goes in the last bin
    idx = np.clip(np.digitize(s, edges[1:-1], right=False), 0, n_bins - 1)
    count = np.bincount(idx, minlength=n_bins)
    with np.errstate(invalid="ignore", divide="ignore"):
        conf = np.bincount(idx, weights=s, minlength=n_bins) / count
        frac = np.bincount(idx, weights=y, minlength=n_bins) / count
    return {"edges": edges, "count": count, "mean_score": conf, "frac_pos": frac}


def expected_calibration_error(y_true, y_score, n_bins: int = 10) -> float:
    """ECE = sum_b (n_b / N) * |frac_pos_b - mean_score_b| over non-empty bins."""
    b = reliability_bins(y_true, y_score, n_bins)
    n = b["count"].sum()
    ok = b["count"] > 0
    gap = np.abs(b["frac_pos"][ok] - b["mean_score"][ok])
    return float((b["count"][ok] / n * gap).sum())
