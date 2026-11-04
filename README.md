# OdorMap

Predicts **odor descriptors of single molecules** (e.g. "vanilla", "fruity",
"sulfurous") from their chemical structure (SMILES), trained on the
GoodScents + Leffingwell dataset of 4,983 molecules / 138 descriptors curated by
Lee et al. 2023 (*Science*, DOI 10.1126/science.ade4401).

> **Scope:** this models catalog-style descriptor labels for individual pure
> molecules. It is **not** a model of real-world odor sensing: it knows nothing
> about mixtures, concentration, odor thresholds, individual perception, or
> electronic-nose / sensor data. There is no "odorless" class, so it will return
> descriptors for any valid molecule.

This is chunk 1: a CPU-only baseline (Morgan fingerprints + one-vs-rest
logistic regression).

## Setup

Python 3.10+; CPU only, no GPU or paid APIs.

```bash
pip install -r requirements.txt
```

## Fetch the data

The dataset is not stored in git (see [DATA.md](DATA.md) for provenance and an
open licensing question).

```bash
python scripts/fetch_data.py
```

## Audit the data

```bash
python scripts/audit.py
```

Writes [results/audit.md](results/audit.md).

## Run the baseline

```bash
python scripts/run_baseline.py
```

Runs stratified random 5-fold CV and a Bemis-Murcko scaffold 80/20 split,
writes [results/baseline.md](results/baseline.md), and saves the model refit on
all data to `models/baseline_lr.joblib` (git-ignored). Takes well under a minute
on a laptop CPU.

## Predict

```bash
python scripts/predict.py "COc1cc(C=O)ccc1O"
```

Prints the top-10 descriptors with probabilities. Examples:
[results/predict_examples.md](results/predict_examples.md)
(regenerate with `python scripts/make_predict_examples.py`).

## Run tests

```bash
python -m pytest -q
```

Tests that need the dataset are skipped if `data/` has not been fetched.

## Layout

```
odormap/          library code: data loading, features, splits, model/metrics
scripts/          fetch_data, audit, run_baseline, predict, make_predict_examples
tests/            pytest suite
results/          audit.md, baseline.md, predict_examples.md
DATA.md           dataset provenance and licensing notes
```
