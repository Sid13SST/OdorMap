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

A CPU-only baseline (Morgan fingerprints + one-vs-rest logistic regression)
with a local Streamlit demo app.

> **Scores, not probabilities:** the numbers the model outputs are model
> confidence **scores**. They are **not calibrated probabilities**: on the
> held-out scaffold test set, pooled ECE is 0.080 and (molecule, descriptor)
> pairs scored 0.9–1.0 were positive only 47% of the time
> ([results/calibration.md](results/calibration.md)). Use them to rank
> descriptors, not as chances.

## Demo

```bash
pip install -r requirements.txt
python scripts/fetch_data.py && python scripts/run_baseline.py   # creates the model
streamlit run app.py
```

Runs locally on CPU; no paid APIs, GPU or external services. Enter a SMILES
string or pick one of 8 examples (4 in the dataset, 4 not). The app shows the
2D structure, the top-10 descriptors with their scores, and a **training
membership flag**:

- **in training data (memorization possible)** — the saved model is refit on
  all 4,983 molecules, so for a dataset molecule the scores can reflect
  memorized catalog labels, not generalization;
- **new molecule (true generalization)** — not in the dataset (exact match on
  canonical SMILES, stereochemistry ignored). Close analogs may still be in the
  training set.

Vanillin (in the dataset):

![App with vanillin, flagged as in training data](docs/screenshots/app_vanillin.png)

5-Propylvanillin, a vanillin analog that is not in the dataset:

![App with 5-propylvanillin, flagged as a new molecule](docs/screenshots/app_new_molecule.png)

Screenshots are produced by `python scripts/screenshot_app.py` (needs
`pip install -r requirements-dev.txt` and `python -m playwright install chromium`,
or `CHROMIUM_PATH` pointing at an existing Chromium).

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

## Results

From [results/baseline.md](results/baseline.md) and
[results/calibration.md](results/calibration.md):

| Split | macro ROC-AUC | micro ROC-AUC | macro F1@0.5 | mAP |
|---|---|---|---|---|
| Random 5-fold CV (mean ± sd) | 0.828 ± 0.006 | 0.885 ± 0.003 | 0.285 ± 0.009 | 0.279 ± 0.011 |
| Scaffold split (single split) | 0.735 | 0.834 | 0.169 | 0.153 |

**Caveats on the scaffold split:**

- The acyclic (empty) scaffold group — 2,236 molecules, **45% of the dataset** —
  is forced into the training set, so the scaffold **test set contains no acyclic
  molecules** and its distribution differs from the full dataset.
- It is a **single split (one seed)**, so the scaffold numbers carry **no
  variance estimate**.

**Calibration:** pooled ECE = 0.080 (10 bins, 36 labels with ≥ 30 test
positives, scaffold test set). Scores ≥ 0.5 are strongly over-confident, so
outputs are reported as scores, not probabilities.

**Low macro F1 and label frequency:** per-label F1@0.5 is moderately
rank-correlated with the label's number of test positives (Spearman ρ = 0.54;
ρ = 0.31 with train positives), while per-label ROC-AUC is not (ρ = −0.04).
Rare labels have lower F1 but are ranked about as well; the role of the fixed
0.5 threshold and of over-confident scores is a hypothesis that has not been
separated from rarity.

Calibration is measured with `python scripts/calibration.py`.

## Predict

```bash
python scripts/predict.py "COc1cc(C=O)ccc1O"
```

Prints the training-membership flag and the top-10 descriptors with their
scores (model confidence, not calibrated probabilities). Examples:
[results/predict_examples.md](results/predict_examples.md)
(regenerate with `python scripts/make_predict_examples.py`).

## Run tests

```bash
python -m pytest -q
```

Tests that need the dataset or the trained model are skipped if they are missing.

## Layout

```
app.py            Streamlit demo app
odormap/          library code: data loading, features, splits, model/metrics,
                  inference (membership flag), calibration
scripts/          fetch_data, audit, run_baseline, calibration, predict,
                  make_predict_examples, screenshot_app
tests/            pytest suite (incl. Streamlit AppTest tests)
results/          audit.md, baseline.md, calibration.md (+ reliability PNG),
                  predict_examples.md
docs/screenshots/ app screenshots used in this README
DATA.md           dataset provenance and licensing notes
```
