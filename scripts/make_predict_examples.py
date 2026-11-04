"""Run scripts/predict.py on a few known molecules and write results/predict_examples.md."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from odormap.data import SMILES_COL, load_dataset  # noqa: E402
from odormap.inference import membership_key as nonstereo  # noqa: E402

EXAMPLES = [
    ("vanillin", "COc1cc(C=O)ccc1O"),
    ("cinnamaldehyde", "O=C/C=C/c1ccccc1"),
    ("isoamyl acetate", "CC(=O)OCCC(C)C"),
    ("geraniol", "CC(C)=CCC/C(C)=C/CO"),
    ("limonene", "CC1=CCC(CC1)C(=C)C"),
    ("dimethyl sulfide", "CSC"),
    ("isovanillin", "O=Cc1ccc(OC)c(O)c1"),
    ("ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
]


def main() -> int:
    df, _ = load_dataset()
    catalog = {nonstereo(s): d for s, d in zip(df[SMILES_COL], df["descriptors"])}
    L = ["# Example predictions\n",
         "Produced by `python scripts/make_predict_examples.py`, which calls "
         "`python scripts/predict.py <SMILES>` and pastes its stdout verbatim.\n",
         "**Caveat:** the model in `models/baseline_lr.joblib` is trained on **all** "
         "4,983 molecules. For molecules that are in the dataset, these outputs show "
         "fit to training labels, not generalization. Generalization estimates are in "
         "`results/baseline.md`. Molecules marked *not in dataset* are not found in the "
         "training data (canonical-SMILES match, stereo ignored); their predictions are "
         "unvalidated, since there is no ground truth for them and close structural "
         "analogs may exist in the training set. The `Training membership` line is "
         "printed by `predict.py` itself.\n\n"
         "Numbers are model confidence **scores**, not calibrated probabilities "
         "(see `results/calibration.md`).\n"]
    for name, smi in EXAMPLES:
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "predict.py"), smi],
                             capture_output=True, text=True, check=True).stdout
        cat = catalog.get(nonstereo(smi))
        L.append(f"## {name}\n")
        if cat is None:
            L.append("*Not in dataset (prediction unvalidated).*\n")
        else:
            L.append(f"*In training set.* Catalog descriptors: `{cat}`\n")
        L.append("```\n" + out.rstrip() + "\n```\n")
    L.append("Note: the label set has no 'odorless' class, so the model always returns "
             "some descriptors with nonzero score, even for molecules (such as "
             "ibuprofen) that are not regarded as odorants.\n")
    out_path = ROOT / "results" / "predict_examples.md"
    out_path.write_text("\n".join(L), encoding="utf-8")
    print(out_path.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
