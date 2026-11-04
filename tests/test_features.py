import numpy as np
import pytest

from odormap.features import (
    N_BITS, canonical_smiles, featurize, morgan_fp, murcko_scaffold,
)

VANILLIN = "COc1cc(C=O)ccc1O"


def test_morgan_shape_dtype_binary():
    fp = morgan_fp(VANILLIN)
    assert fp.shape == (N_BITS,) == (2048,)
    assert fp.dtype == np.uint8
    assert set(np.unique(fp)) <= {0, 1}
    assert fp.sum() > 0


def test_morgan_invariant_to_smiles_writing():
    # Same molecule written two ways -> identical fingerprint.
    assert np.array_equal(morgan_fp(VANILLIN), morgan_fp("O=Cc1ccc(O)c(OC)c1"))


def test_morgan_differs_between_molecules():
    assert not np.array_equal(morgan_fp(VANILLIN), morgan_fp("CCO"))


def test_morgan_deterministic():
    assert np.array_equal(morgan_fp(VANILLIN), morgan_fp(VANILLIN))


@pytest.mark.parametrize("bad", ["", "not_a_smiles", "C1CC", None])
def test_invalid_smiles_raise(bad):
    with pytest.raises(ValueError):
        morgan_fp(bad)


def test_featurize_stacks():
    X = featurize([VANILLIN, "CCO", "CSC"])
    assert X.shape == (3, 2048)


def test_canonical_smiles():
    assert canonical_smiles("OCC") == canonical_smiles("CCO")
    assert canonical_smiles("garbage") is None


def test_murcko_scaffold():
    assert murcko_scaffold(VANILLIN) == "c1ccccc1"
    assert murcko_scaffold("CCCCO") == ""  # acyclic
