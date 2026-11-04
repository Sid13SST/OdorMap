import numpy as np

from odormap.model import build_model, evaluate


def test_model_fits_and_evaluates_on_toy():
    rng = np.random.default_rng(0)
    X = (rng.random((120, 32)) < 0.3).astype(np.uint8)
    Y = np.stack([X[:, 0], X[:, 1] | X[:, 2], 1 - X[:, 3]], axis=1)
    m = build_model(n_jobs=1).fit(X, Y)
    P = m.predict_proba(X)
    assert P.shape == Y.shape
    r = evaluate(Y, P)
    assert r["macro_roc_auc"] > 0.9
    assert r["n_labels_skipped"] == 0


def test_evaluate_skips_constant_labels():
    Y = np.array([[1, 0], [0, 0], [1, 0], [0, 0]])
    P = np.array([[0.9, 0.1], [0.2, 0.1], [0.8, 0.3], [0.1, 0.2]])
    r = evaluate(Y, P)
    assert r["n_labels_skipped"] == 1
    assert r["macro_roc_auc"] == 1.0
