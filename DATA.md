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

## Distributions of the curated file

| Distribution | License | Location |
|---|---|---|
| OpenPOM (open-source replication of the POM model), file `curated_GS_LF_merged_4983.csv` | MIT | <https://github.com/ARY2260/openpom> |
| Authors' data/code bundle for Lee et al. 2023 | Apache-2.0 | Zenodo, DOI [10.5281/zenodo.7992168](https://doi.org/10.5281/zenodo.7992168) |

This project downloads from the OpenPOM GitHub repository.

## OPEN QUESTION — must be resolved before this repo is made public

The MIT (OpenPOM) and Apache-2.0 (Zenodo) licenses cover those projects'
redistribution of the *curated* file. They do not by themselves establish the
redistribution terms of the **original GoodScents and Leffingwell catalogs**
from which the odor descriptors were derived. Those terms have **not been
verified** for this project.

Until that is checked:

- Do not commit the CSV (or derived per-molecule label tables) to this repository.
- Treat any trained model artifacts as private.
- Before making this repository public, verify the GoodScents and Leffingwell
  terms of use / redistribution conditions and record the outcome here.
