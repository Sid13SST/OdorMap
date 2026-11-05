"""The train-if-missing path used by the app on a fresh clone / cloud deploy.

The network download is mocked and training runs on a tiny synthetic CSV, so
these tests need neither the real dataset nor a trained model.
"""
from pathlib import Path

import joblib
import pandas as pd
import pytest
import requests

import odormap.fetch as fetch_mod
import odormap.inference as inference
import odormap.train as train
from odormap.fetch import BEHAVIOR_URL, MOLECULES_URL, FetchError
from odormap.inference import Predictor

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
APP = str(Path(__file__).resolve().parents[1] / "app.py")

TOY_CSV = """CID,MolecularWeight,IsomericSMILES,IUPACName,name,vanilla,fruity
1,152.1,COc1cc(C=O)ccc1O,,vanillin,1,0
2,130.2,CC(=O)OCCC(C)C,,isoamyl acetate,0,1
3,102.1,CCOC(=O)CC,,ethyl propionate,0,1
4,122.1,O=Cc1ccc(O)cc1,,4-hydroxybenzaldehyde,1,0
5,74.1,CCCCO,,butanol,0,0
6,130.2,CC(C)CCOC(C)=O,,isoamyl acetate (alt.),0,1
"""
TOY_MOLECULES = """CID,MolecularWeight,IsomericSMILES,IUPACName,name
1,152.1,COc1cc(C=O)ccc1O,,vanillin
2,130.2,CC(=O)OCCC(C)C,,isoamyl acetate
"""
TOY_BEHAVIOR = """Stimulus,vanilla,fruity
2,0,1
1,1,0
"""
BUNDLE_KEYS = {"model", "labels", "radius", "n_bits", "training_keys"}


def _fake_fetch(calls):
    def fake(out, *a, **k):
        calls.append(Path(out))
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(TOY_CSV, encoding="utf-8")
        return Path(out)
    return fake


def test_ensure_model_fetches_and_trains_when_missing(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(train, "fetch", _fake_fetch(calls))
    data, model = tmp_path / "data" / "d.csv", tmp_path / "models" / "m.joblib"
    assert train.ensure_model(model, data) == model
    assert calls == [data] and model.exists()
    bundle = joblib.load(model)
    assert set(bundle) == BUNDLE_KEYS  # same schema as scripts/run_baseline.py
    assert bundle["labels"] == ["vanilla", "fruity"]
    pred = Predictor.load(model)
    assert pred.is_in_training("COc1cc(C=O)ccc1O")
    assert [l for l, _ in pred.predict("COc1cc(C=O)ccc1O").scores][0] == "vanilla"


def test_ensure_model_does_nothing_when_model_exists(tmp_path, monkeypatch):
    model = tmp_path / "m.joblib"
    model.write_bytes(b"existing")

    def boom(*a, **k):
        raise AssertionError("must not fetch or train when the model exists")

    monkeypatch.setattr(train, "fetch", boom)
    monkeypatch.setattr(train, "train_and_save", boom)
    assert train.ensure_model(model, tmp_path / "missing.csv") == model


def test_ensure_model_reuses_existing_data(tmp_path, monkeypatch):
    data = tmp_path / "d.csv"
    data.write_text(TOY_CSV, encoding="utf-8")
    monkeypatch.setattr(train, "fetch", lambda *a, **k: pytest.fail("data present"))
    assert train.ensure_model(tmp_path / "m.joblib", data).exists()


def test_fetch_failure_raises_readable_error(tmp_path, monkeypatch):
    def down(url, timeout):
        raise requests.ConnectionError("no route to host")

    monkeypatch.setattr(fetch_mod, "_download", down)
    monkeypatch.setattr(fetch_mod.time, "sleep", lambda s: None)
    out = tmp_path / "d.csv"
    with pytest.raises(FetchError) as e:
        fetch_mod.fetch(out)
    assert MOLECULES_URL in str(e.value) and "attempts" in str(e.value)
    assert not out.exists()


def test_fetch_joins_molecules_and_labels_on_cid(tmp_path, monkeypatch):
    texts = {MOLECULES_URL: TOY_MOLECULES, BEHAVIOR_URL: TOY_BEHAVIOR}
    monkeypatch.setattr(fetch_mod, "_download", lambda url, timeout: texts[url])
    out = fetch_mod.fetch(tmp_path / "d.csv")
    df = pd.read_csv(out)
    assert list(df.columns) == ["CID", "MolecularWeight", "IsomericSMILES", "IUPACName",
                                "name", "vanilla", "fruity"]
    row = df.set_index("name")
    assert row.loc["vanillin", ["vanilla", "fruity"]].tolist() == [1, 0]
    assert row.loc["isoamyl acetate", ["vanilla", "fruity"]].tolist() == [0, 1]


def test_fetch_rejects_mismatched_ids(tmp_path, monkeypatch):
    texts = {MOLECULES_URL: TOY_MOLECULES, BEHAVIOR_URL: "Stimulus,vanilla,fruity\n9,1,0\n"}
    monkeypatch.setattr(fetch_mod, "_download", lambda url, timeout: texts[url])
    with pytest.raises(FetchError, match="do not match"):
        fetch_mod.fetch(tmp_path / "d.csv")
    assert not (tmp_path / "d.csv").exists()


def test_fetch_rejects_unexpected_content(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_mod, "_download", lambda url, timeout: "<html>404</html>")
    with pytest.raises(FetchError, match="Unexpected file header"):
        fetch_mod.fetch(tmp_path / "d.csv")
    assert not (tmp_path / "d.csv").exists()


def test_app_trains_on_first_run_when_model_missing(tmp_path, monkeypatch):
    model = tmp_path / "models" / "baseline_lr.joblib"
    monkeypatch.setattr(inference, "MODEL_PATH", model)
    calls = []

    def fake_ensure(model_path, *a, **k):
        calls.append(Path(model_path))
        data = tmp_path / "data.csv"
        data.write_text(TOY_CSV, encoding="utf-8")
        return train.train_and_save(data, model_path)

    monkeypatch.setattr(train, "ensure_model", fake_ensure)
    at = streamlit_testing.AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception and not at.error
    assert calls == [model] and model.exists()
    assert any(s.value == "Top-10 odor descriptors" for s in at.subheader)
    assert "in training data (memorization possible)" in at.warning[0].value

    # Later reruns reuse the cached predictor: no second training.
    at.text_input(key="smiles").input("CCCc1cc(C=O)cc(OC)c1O").run()
    assert not at.exception and calls == [model]
    assert "Not found in training data" in at.warning[0].value


def test_app_shows_readable_error_when_fetch_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(inference, "MODEL_PATH", tmp_path / "models" / "m.joblib")

    def fail(*a, **k):
        raise FetchError(f"Could not download the dataset from {MOLECULES_URL} after 3 attempts.")

    monkeypatch.setattr(train, "ensure_model", fail)
    at = streamlit_testing.AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert len(at.error) == 1
    msg = at.error[0].value
    assert "Could not download the training data" in msg
    assert MOLECULES_URL in msg and BEHAVIOR_URL in msg
    assert any("CC-BY-NC 4.0" in c.value for c in at.caption)  # footer still shown
    assert not any(s.value == "Top-10 odor descriptors" for s in at.subheader)
