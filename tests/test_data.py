import pandas as pd
import pytest

from conftest import requires_data
from odormap.data import SMILES_COL, label_columns, load_dataset, validate_dataframe
from odormap.features import canonical_smiles, mol_from_smiles
from odormap.inference import membership_key


def _toy():
    return pd.DataFrame({
        "CID": [702, 1068], "MolecularWeight": [46.07, 62.13], SMILES_COL: ["CCO", "CSC"],
        "IUPACName": ["ethanol", "methylsulfanylmethane"], "name": ["ethanol", "dimethyl sulfide"],
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
    assert len(df) == 3522
    assert len(labels) == 113
    assert df["CID"].is_unique
    assert all(mol_from_smiles(s) is not None for s in df[SMILES_COL])
    canon = [canonical_smiles(s) for s in df[SMILES_COL]]
    assert len(set(canon)) == len(canon)  # unique with stereochemistry
    assert (df[labels].sum(axis=1) > 0).all()


@requires_data
def test_stereoisomers_share_a_stereo_free_key():
    # 3,522 isomeric SMILES collapse to 3,400 stereo-free structures; this is why
    # random CV groups stereoisomers into the same fold (see odormap/splits.py).
    df, _ = load_dataset()
    assert len({membership_key(s) for s in df[SMILES_COL]}) == 3400
