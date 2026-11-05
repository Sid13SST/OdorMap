"""Run scripts/predict.py on a few known molecules and write results/predict_examples.md."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from odormap.data import NAME_COL, SMILES_COL, load_dataset  # noqa: E402
from odormap.inference import Predictor, membership_key as nonstereo  # noqa: E402

EXAMPLES = [
    ("vanillin", "COc1cc(C=O)ccc1O"),
    ("cinnamaldehyde", "O=C/C=C/c1ccccc1"),
    ("isoamyl acetate", "CC(=O)OCCC(C)C"),
    ("geraniol", "CC(C)=CCC/C(C)=C/CO"),
    ("limonene", "CC1=CCC(CC1)C(=C)C"),
    ("dimethyl sulfide", "CSC"),
    ("isovanillin", "O=Cc1ccc(OC)c(O)c1"),
    ("5-propylvanillin", "CCCc1cc(C=O)cc(OC)c1O"),
    ("ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
]


def main() -> int:
    df, labels = load_dataset()
    # Stereoisomers share a stereo-free key, so one key can map to several rows.
    catalog: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        desc = ";".join(l for l in labels if row[l] == 1)
        catalog.setdefault(nonstereo(row[SMILES_COL]), []).append(
            f"{row[NAME_COL]}: {desc}")
    L = ["# Example predictions\n",
         "Produced by `python scripts/make_predict_examples.py`, which calls "
         "`python scripts/predict.py <SMILES>` and pastes its stdout verbatim.\n",
         "**Caveat:** the model in `models/baseline_lr.joblib` is trained on **all** "
         "3,522 Leffingwell molecules. For molecules that are in the dataset, these outputs show "
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
            rows = "; ".join(f"`{c}`" for c in cat)
            L.append(f"*In training set.* Catalog descriptors ({len(cat)} row(s) with this "
                     f"stereo-free structure): {rows}\n")
        L.append("```\n" + out.rstrip() + "\n```\n")
    # The Leffingwell label set includes 'odorless', scored like any other label.
    pred = Predictor.load()
    n_odorless = int(df["odorless"].sum())
    lines = []
    for name, smi in EXAMPLES:
        ranked = pred.predict(smi, top=len(pred.labels)).scores
        rank = next(i for i, (lab, _) in enumerate(ranked, 1) if lab == "odorless")
        lines.append(f"| {name} | {dict(ranked)['odorless']:.3f} | {rank} of {len(ranked)} |")
    L.append("## The `odorless` label\n")
    L.append(f"The Leffingwell label set includes an `odorless` label ({n_odorless} positive "
             "molecules). It is one of the independent per-label scores, not an exclusive "
             "class, so every molecule still gets nonzero scores for other descriptors. "
             "Measured `odorless` score and its rank among all labels for the examples "
             "above:\n")
    L.append("| Molecule | `odorless` score | Rank |\n|---|---|---|")
    L.extend(lines)
    L.append("")
    out_path = ROOT / "results" / "predict_examples.md"
    out_path.write_text("\n".join(L), encoding="utf-8")
    print(out_path.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
