import numpy as np
import pandas as pd
import pytest

from conftest import requires_data
from odormap.data import SMILES_COL, label_columns, load_dataset, validate_dataframe
from odormap.features import canonical_smiles, mol_from_smiles


def _toy():
    return pd.DataFrame({
        SMILES_COL: ["CCO", "CSC"], "descriptors": ["alcoholic", "sulfurous"],
        "alcoholic": [1, 0], "sulfurous": [0, 1],
    })


def test_validate_accepts_toy():
    validate_dataframe(_toy())
    assert label_columns(_toy()) == ["alcoholic", "sulfurous"]


def test_validate_rejects_missing_column():
    with pytest.raises(ValueError):
        validate_dataframe(_toy().drop(columns=[SMILES_COL]))


def test_validate_rejects_nonbinary_labels():
    df = _toy()
    df.loc[0, "alcoholic"] = 2
    with pytest.raises(ValueError):
        validate_dataframe(df)


def test_validate_rejects_null_smiles():
    df = _toy()
    df.loc[0, SMILES_COL] = None
    with pytest.raises(ValueError):
        validate_dataframe(df)


def test_missing_file_message(tmp_path):
    with pytest.raises(FileNotFoundError, match="fetch_data"):
        load_dataset(tmp_path / "nope.csv")


@requires_data
def test_real_dataset_shape_and_validity():
    df, labels = load_dataset()
    assert len(df) == 4983
    assert len(labels) == 138
    assert all(mol_from_smiles(s) is not None for s in df[SMILES_COL])
    canon = [canonical_smiles(s) for s in df[SMILES_COL]]
    assert len(set(canon)) == len(canon)
    assert (df[labels].sum(axis=1) > 0).all()


@requires_data
def test_descriptor_string_matches_label_columns():
    df, labels = load_dataset()
    Y = df[labels].to_numpy()
    lab = np.array(labels)
    for i, d in enumerate(df["descriptors"]):
        assert set(d.split(";")) == set(lab[Y[i] == 1])
