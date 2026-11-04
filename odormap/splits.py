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
