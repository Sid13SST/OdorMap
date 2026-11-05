# Data provenance

This repository does **not** contain the dataset. Fetch it with:

```bash
python scripts/fetch_data.py
```

which saves `data/curated_GS_LF_merged_4983.csv` (`data/` is git-ignored).

## Exact download URL

<https://raw.githubusercontent.com/ARY2260/openpom/main/openpom/data/curated_datasets/curated_GS_LF_merged_4983.csv>

The file has 4,983 rows and 140 columns: `nonStereoSMILES` (SMILES with
stereochemistry removed), `descriptors` (semicolon-separated odor labels), and
138 binary (0/1) label columns.

## Original source catalogs

The odor descriptors were compiled from two perfumery / flavor industry catalogs:

- **The Good Scents Company** information system (GoodScents), <http://www.thegoodscentscompany.com/>
- **Leffingwell & Associates** PMP 2001 database (Leffingwell), <http://www.leffingwell.com/>

The two sources were merged, curated, and harmonized to a shared descriptor
vocabulary by the authors of:

> Lee, B. K., Mayhew, E. J., Sanchez-Lengeling, B., Wei, J. N., Qian, W. W.,
> Little, K. A., Andres, M., Nguyen, B. B., Moloy, T., Yasonik, J., Parker, J. K.,
> Gerkin, R. C., Mainland, J. D., & Wiltschko, A. B. (2023).
> *A principal odor map unifies diverse tasks in olfactory perception.*
> Science 381(6661), 999–1006. DOI: [10.1126/science.ade4401](https://doi.org/10.1126/science.ade4401)

## Where the curated file comes from, and what its licenses cover

| Source | License | Contains `curated_GS_LF_merged_4983.csv`? |
|---|---|---|
| OpenPOM (third-party open-source replication of the POM model), <https://github.com/ARY2260/openpom> | MIT | Yes — this project downloads it from there |
| Authors' Zenodo bundle for Lee et al. 2023, DOI [10.5281/zenodo.7992168](https://doi.org/10.5281/zenodo.7992168) | Apache-2.0 | **No** — it contains only psychophysics / figure data, not the GoodScents + Leffingwell training catalog |

Findings (checked for this project):

- **The Zenodo bundle does not contain the training catalog.** Its Apache-2.0
  license therefore says nothing about `curated_GS_LF_merged_4983.csv`.
- **The POM paper does not freely license the training catalog.** Its data
  availability statement does not place the GoodScents + Leffingwell data
  under an open license.
- **GoodScents data is proprietary** to The Good Scents Company.
- **OpenPOM's MIT license covers OpenPOM's code**, not the underlying
  GoodScents / Leffingwell data that the CSV in that repository was derived from.

## Conclusion: redistribution terms are UNRESOLVED

No source found grants redistribution rights for the training catalog.
Until that changes:

- **The CSV is not committed** to this repository (`data/` is git-ignored).
  Do not commit it, or derived per-molecule label tables.
- **The trained model file is not committed either** (`models/` is
  git-ignored). `models/baseline_lr.joblib` is a derived artifact of the
  dataset (it also stores the training molecules' canonical SMILES for the
  membership flag), so it falls under the same unresolved terms.
- **The deployed demo app does not bundle either file.** On first start it
  downloads the CSV at runtime from the OpenPOM URL above and trains the model
  in the running process (see `odormap/train.py` and the README's deploy
  section). The app therefore depends on that URL staying available.
