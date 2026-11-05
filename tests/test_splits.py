import numpy as np
import pytest

from conftest import requires_data
from odormap.data import SMILES_COL, load_dataset
from odormap.features import murcko_scaffold
from odormap.splits import iterative_stratified_kfold, scaffold_split

TOY = [
    "CCO", "CCCO", "CCCCO",                      # acyclic
    "Cc1ccccc1", "CCc1ccccc1", "Oc1ccccc1",      # benzene
    "CC1CCCCC1", "OC1CCCCC1",                    # cyclohexane
    "c1ccoc1", "Cc1ccoc1",                       # furan
    "c1ccncc1", "Cc1ccncc1",                     # pyridine
    "c1ccsc1", "C1CCOC1",
]


def _check_scaffold_split(smiles, tr, te):
    assert len(set(tr) & set(te)) == 0
    assert sorted(np.concatenate([tr, te]).tolist()) == list(range(len(smiles)))
    tr_sc = {murcko_scaffold(smiles[i]) for i in tr}
    te_sc = {murcko_scaffold(smiles[i]) for i in te}
    assert tr_sc.isdisjoint(te_sc)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_scaffold_split_toy(seed):
    tr, te = scaffold_split(TOY, test_frac=0.3, seed=seed)
    _check_scaffold_split(TOY, tr, te)
    assert len(te) > 0


def test_scaffold_split_deterministic():
    a = scaffold_split(TOY, 0.3, seed=5)
    b = scaffold_split(TOY, 0.3, seed=5)
    assert all(np.array_equal(x, y) for x, y in zip(a, b))


def test_iterative_kfold_partitions():
    rng = np.random.default_rng(0)
    Y = (rng.random((200, 6)) < 0.2).astype(int)
    folds = iterative_stratified_kfold(Y, 5, seed=0)
    tests = np.concatenate([te for _, te in folds])
    assert sorted(tests.tolist()) == list(range(200))
    for tr, te in folds:
        assert set(tr).isdisjoint(te)
        assert len(tr) + len(te) == 200
    # each label roughly evenly distributed across folds
    for j in range(Y.shape[1]):
        per_fold = [Y[te, j].sum() for _, te in folds]
        assert max(per_fold) - min(per_fold) <= 2


@requires_data
def test_scaffold_split_real_no_shared_scaffolds():
    df, _ = load_dataset()
    smiles = df[SMILES_COL].tolist()
    tr, te = scaffold_split(smiles, test_frac=0.2, seed=0)
    _check_scaffold_split(smiles, tr, te)
    assert abs(len(te) / len(smiles) - 0.2) < 0.02


@requires_data
def test_iterative_kfold_real_every_label_in_every_fold():
    df, labels = load_dataset()
    Y = df[labels].to_numpy()
    for _, te in iterative_stratified_kfold(Y, 5, seed=0):
        assert (Y[te].sum(axis=0) > 0).all()


def test_grouped_kfold_keeps_groups_together_and_partitions_rows():
    from odormap.splits import grouped_stratified_kfold
    rng = np.random.default_rng(0)
    groups = [i // 3 if i < 30 else i for i in range(60)]  # 10 triplets + 30 singletons
    Y = rng.random((60, 4)) < 0.4
    folds = grouped_stratified_kfold(Y, groups, n_splits=5, seed=0)
    seen = np.concatenate([te for _, te in folds])
    assert sorted(seen.tolist()) == list(range(60))
    for tr, te in folds:
        assert {groups[i] for i in tr}.isdisjoint({groups[i] for i in te})


@requires_data
def test_real_data_grouped_kfold_separates_stereo_free_structures():
    from odormap.inference import membership_key
    from odormap.splits import grouped_stratified_kfold
    df, labels = load_dataset()
    keys = [membership_key(s) for s in df[SMILES_COL]]
    for tr, te in grouped_stratified_kfold(df[labels].to_numpy(), keys, 5, 0):
        assert {keys[i] for i in tr}.isdisjoint({keys[i] for i in te})
