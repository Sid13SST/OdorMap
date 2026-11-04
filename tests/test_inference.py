import numpy as np
import pytest

from conftest import requires_data
from odormap.features import featurize
from odormap.inference import (
    IN_TRAINING, MODEL_PATH, NEW_MOLECULE, Predictor, membership_key, membership_keys,
)
from odormap.model import build_model

VANILLIN = "COc1cc(C=O)ccc1O"
PROPYL_VANILLIN = "CCCc1cc(C=O)cc(OC)c1O"  # vanillin analog, not in the dataset


def test_membership_key_ignores_writing_and_stereo():
    assert membership_key(VANILLIN) == membership_key("O=Cc1ccc(O)c(OC)c1")
    assert membership_key("C/C=C/C") == membership_key("C/C=C\\C") == "CC=CC"
    assert membership_key("not a smiles") is None


def _toy_predictor(train_smiles):
    X = featurize(train_smiles)
    Y = np.array([[1, 0], [0, 1], [1, 1], [0, 0]])
    model = build_model(n_jobs=1).fit(X, Y)
    return Predictor(model, ["a", "b"], membership_keys(train_smiles))


def test_flag_distinguishes_training_and_new_molecules():
    pred = _toy_predictor([VANILLIN, "CCO", "CCCC(=O)O", "c1ccccc1"])
    seen = pred.predict("O=Cc1ccc(O)c(OC)c1")  # vanillin, written differently
    new = pred.predict(PROPYL_VANILLIN)
    assert seen.in_training and seen.membership == IN_TRAINING
    assert not new.in_training and new.membership == NEW_MOLECULE
    assert [l for l, _ in seen.scores] and all(0 <= s <= 1 for _, s in seen.scores)


def test_invalid_smiles_raises():
    pred = _toy_predictor([VANILLIN, "CCO", "CCCC(=O)O", "c1ccccc1"])
    with pytest.raises(ValueError):
        pred.predict("C1CC(")


@requires_data
@pytest.mark.skipif(not MODEL_PATH.exists(), reason="model not trained")
def test_saved_model_flags_vanillin_in_training_and_analog_new():
    p = Predictor.load()
    assert len(p.training_keys) == 4983
    assert p.predict(VANILLIN).membership == IN_TRAINING
    assert p.predict(PROPYL_VANILLIN).membership == NEW_MOLECULE
