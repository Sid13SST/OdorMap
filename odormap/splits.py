"""Train/test splitting utilities."""
from __future__ import annotations

from collections import defaultdict
from typing import Sequence

import numpy as np

from .features import murcko_scaffold


def scaffold_split(
    smiles: Sequence[str], test_frac: float = 0.2, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Bemis-Murcko scaffold split with no scaffold shared across train/test.

    Scaffold groups are shuffled (seeded) and greedily assigned to the test set
    until it reaches ``test_frac`` of molecules. The largest group (typically
    the acyclic '' scaffold, or benzene) is forced into train so it cannot
    dominate the test set. Returns (train_idx, test_idx).
    """
    groups: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(smiles):
        groups[murcko_scaffold(s)].append(i)

    keys = sorted(groups)  # deterministic before shuffling
    rng = np.random.default_rng(seed)
    rng.shuffle(keys)
    largest = max(keys, key=lambda k: len(groups[k]))

    n_test_target = int(round(test_frac * len(smiles)))
    train, test = [], []
    for k in keys:
        idx = groups[k]
        if k != largest and len(test) + len(idx) <= n_test_target:
            test.extend(idx)
        else:
            train.extend(idx)
    return np.array(sorted(train)), np.array(sorted(test))


def iterative_stratified_kfold(
    Y: np.ndarray, n_splits: int = 5, seed: int = 0
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Multi-label stratified K-fold (iterative stratification, Sechidis et al. 2011).

    Implemented here to avoid an extra dependency. Returns a list of
    (train_idx, test_idx) pairs; folds partition all rows.
    """
    Y = np.asarray(Y).astype(bool)
    n, n_labels = Y.shape
    rng = np.random.default_rng(seed)
    ratios = np.full(n_splits, 1.0 / n_splits)
    desired_total = ratios * n
    desired_label = np.outer(ratios, Y.sum(axis=0)).astype(float)  # (k, L)
    fold_of = np.full(n, -1)
    remaining = np.ones(n, dtype=bool)

    while remaining.any():
        counts = Y[remaining].sum(axis=0)
        active = np.where(counts > 0)[0]
        if active.size == 0:
            # Rows with no positive labels: spread by remaining capacity.
            for i in rng.permutation(np.where(remaining)[0]):
                f = int(np.argmax(desired_total + rng.random(n_splits) * 1e-6))
                fold_of[i] = f
                desired_total[f] -= 1
            break
        # Label with the fewest remaining positives (ties broken randomly).
        min_c = counts[active].min()
        lab = rng.choice(active[counts[active] == min_c])
        rows = np.where(remaining & Y[:, lab])[0]
        for i in rng.permutation(rows):
            d = desired_label[:, lab]
            cand = np.where(d == d.max())[0]
            if cand.size > 1:
                t = desired_total[cand]
                cand = cand[t == t.max()]
            f = int(rng.choice(cand))
            fold_of[i] = f
            remaining[i] = False
            desired_label[f, Y[i]] -= 1
            desired_total[f] -= 1

    all_idx = np.arange(n)
    return [(all_idx[fold_of != k], all_idx[fold_of == k]) for k in range(n_splits)]


def grouped_stratified_kfold(
    Y: np.ndarray, groups: Sequence, n_splits: int = 5, seed: int = 0
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Iterative-stratified K-fold over *groups* of rows; a group never spans folds.

    Used to keep stereoisomers (same stereo-free SMILES, hence identical
    non-chiral Morgan fingerprints) in the same fold. Each group is stratified
    by the union (logical OR) of its rows' labels. Returns (train_idx, test_idx)
    row-index pairs; folds partition all rows.
    """
    Y = np.asarray(Y).astype(bool)
    keys = list(dict.fromkeys(groups))  # first-seen order, deterministic
    pos = {k: i for i, k in enumerate(keys)}
    g = np.array([pos[k] for k in groups])
    Yg = np.zeros((len(keys), Y.shape[1]), dtype=bool)
    np.logical_or.at(Yg, g, Y)
    all_idx = np.arange(len(g))
    out = []
    for _, te_g in iterative_stratified_kfold(Yg, n_splits, seed):
        te = np.isin(g, te_g)
        out.append((all_idx[~te], all_idx[te]))
    return out
