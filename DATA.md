# Data provenance

This repository does **not** contain the dataset. Fetch it with:

```bash
python scripts/fetch_data.py
```

which saves `data/leffingwell.csv` (`data/` is git-ignored).

## Dataset

**Leffingwell Odor Dataset** — expert-labeled odor descriptors for single
molecules, curated and cleaned by Sanchez-Lengeling et al. from the
Leffingwell PMP 2001 database.

- **Canonical record:** Zenodo, DOI [10.5281/zenodo.4085097](https://doi.org/10.5281/zenodo.4085097)
- **License:** Creative Commons Attribution-NonCommercial 4.0 International
  (**CC-BY-NC 4.0**), <https://creativecommons.org/licenses/by-nc/4.0/>
- **Non-commercial use only.** This project, its trained models and the demo
  app inherit that restriction.

## Exact download URLs

This project downloads the pyrfume project's mirror of the dataset:

- Molecules: <https://raw.githubusercontent.com/pyrfume/pyrfume-data/main/leffingwell/molecules.csv>
  (columns `CID`, `MolecularWeight`, `IsomericSMILES`, `IUPACName`, `name`)
- Labels: <https://raw.githubusercontent.com/pyrfume/pyrfume-data/main/leffingwell/behavior.csv>
  (column `Stimulus` plus one binary 0/1 column per odor descriptor)

Measured on the downloaded files: **3,522 data rows in each file, 113 label
columns**, every value 0 or 1, every molecule with at least one label, and the
`Stimulus` and `CID` keys match one-to-one. Negative `CID` values are the
mirror's IDs for compounds without a PubChem CID. The SMILES column used for
training is `IsomericSMILES`. See [results/audit.md](results/audit.md) for the
full audit.

## License source: the Zenodo record

The pyrfume mirror directory (`pyrfume-data/leffingwell/`) carries **no
LICENSE file** (`leffingwell/LICENSE` returns HTTP 404), although its
`manifest.toml` says "see LICENSE for use restrictions". The MIT `LICENSE` at
the root of the pyrfume-data repository is the pyrfume project's own license
and does not license the Leffingwell data. **The Zenodo record
(10.5281/zenodo.4085097) is therefore the canonical license source**, and its
license, CC-BY-NC 4.0, is the one this project follows. (The mirror's
`manifest.toml` cites DOI 10.5281/zenodo.4085098; the dataset readme it
mirrors, `leffingwell_readme.pdf`, states that the data is "freely available
for research use under the CC-BY-NC license".)

## Required attribution

> Sanchez-Lengeling, B., Wei, J. N., Lee, B. K., Gerkin, R. C.,
> Aspuru-Guzik, A., & Wiltschko, A. B. (2019).
> *Machine Learning for Scent: Learning Generalizable Perceptual
> Representations of Small Molecules.* arXiv:1910.10685.
> <https://arxiv.org/abs/1910.10685>

Original data from **John C. Leffingwell and Associates**, PMP 2001 database.

Dataset record: Leffingwell Odor Dataset, Zenodo,
DOI [10.5281/zenodo.4085097](https://doi.org/10.5281/zenodo.4085097),
licensed [CC-BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

The same attribution and license note are shown in the README and in the demo
app's footer.

## Changes made

- `scripts/fetch_data.py` **joins** the molecules and labels tables on
  `Stimulus = CID` and saves the result as `data/leffingwell.csv`.
- We **trained models** on the joined table (see `results/`).
- **The label data itself was not modified**: no labels were added, removed,
  merged or edited, and no rows were dropped.

## What is and is not committed

- The joined CSV is not committed (`data/` is git-ignored); it is fetched from
  the URLs above.
- The trained model `models/baseline_lr.joblib` is not committed (`models/` is
  git-ignored). It is derived from the dataset (it also stores the training
  molecules' stereo-free canonical SMILES for the membership flag).
- The deployed demo app downloads both CSVs at runtime and trains the model in
  the running process (see `odormap/train.py`), so it depends on the two URLs
  above staying available.
