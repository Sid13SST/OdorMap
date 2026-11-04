from pathlib import Path

import pytest

from conftest import requires_data
from odormap.inference import MODEL_PATH

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
APP = str(Path(__file__).resolve().parents[1] / "app.py")

needs_model = pytest.mark.skipif(not MODEL_PATH.exists(), reason="model not trained")


def _run(smiles=None):
    at = streamlit_testing.AppTest.from_file(APP, default_timeout=60).run()
    if smiles is not None:
        at.text_input(key="smiles").input(smiles).run()
    return at


@requires_data
@needs_model
def test_app_loads_without_exceptions():
    at = _run()
    assert not at.exception
    assert at.title[0].value == "OdorMap"
    assert any("not real-world odor sensing" in c.value for c in at.caption)


@requires_data
@needs_model
def test_valid_smiles_shows_descriptors_and_membership():
    at = _run("COc1cc(C=O)ccc1O")
    assert not at.exception and not at.error
    assert any(s.value == "Top-10 odor descriptors" for s in at.subheader)
    assert len(at.get("image")) == 2  # structure image + score chart
    assert "in training data (memorization possible)" in at.warning[0].value


@requires_data
@needs_model
def test_new_molecule_flagged_as_unvalidated():
    at = _run("CCCc1cc(C=O)cc(OC)c1O")
    assert not at.exception
    assert not at.success  # no green/success styling for an unvalidated prediction
    msg = at.warning[0].value
    assert "Not found in training data" in msg
    assert "unvalidated" in msg and "no ground truth" in msg
    assert "close structural analogs may exist in the training set" in msg
    assert "uncalibrated model confidence" in msg
    assert "generalization" not in msg


@requires_data
@needs_model
def test_invalid_smiles_shows_error():
    at = _run("C1CC(not_smiles")
    assert not at.exception
    assert len(at.error) == 1 and "Invalid SMILES" in at.error[0].value
    assert not any(s.value == "Top-10 odor descriptors" for s in at.subheader)


@requires_data
@needs_model
def test_example_dropdown_sets_smiles():
    at = _run()
    at.selectbox(key="example").select("Isoamyl acetate").run()
    assert at.text_input(key="smiles").value == "CC(=O)OCCC(C)C"
    assert not at.exception and not at.error


@requires_data
@needs_model
def test_typed_smiles_switches_dropdown_to_custom():
    at = _run("CCCc1cc(C=O)cc(OC)c1O")
    assert at.selectbox(key="example").value == "5-Propylvanillin (vanillin analog)"
    at.text_input(key="smiles").input("CCCCO").run()
    assert at.selectbox(key="example").value.startswith("Custom")
