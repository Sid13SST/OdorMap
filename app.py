"""OdorMap demo: predict odor descriptors of a single molecule from SMILES.

Run locally (CPU only, no external services):
    streamlit run app.py

Requires models/baseline_lr.joblib (create with `python scripts/run_baseline.py`).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import streamlit as st  # noqa: E402
from rdkit.Chem import Draw  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odormap.features import mol_from_smiles  # noqa: E402
from odormap.inference import MODEL_PATH, Predictor  # noqa: E402

SCOPE_NOTE = ("Scope: predicts catalog odor descriptors of single pure molecules — "
              "not real-world odor sensing, mixtures, or concentration effects.")
SCORE_NOTE = ("Scores are model confidence, not calibrated probabilities: on held-out "
              "scaffolds, molecules scored 0.9–1.0 for a descriptor had it only ~47% of "
              "the time (results/calibration.md).")

# Training membership of each example is checked live against the model bundle.
EXAMPLES = {
    "Vanillin": "COc1cc(C=O)ccc1O",
    "Cinnamaldehyde": "O=C/C=C/c1ccccc1",
    "Limonene": "CC1=CCC(CC1)C(=C)C",
    "Isoamyl acetate": "CC(=O)OCCC(C)C",
    "5-Propylvanillin (vanillin analog)": "CCCc1cc(C=O)cc(OC)c1O",
    "Isoamyl cyclopropanecarboxylate": "CC(C)CCOC(=O)C1CC1",
    "3-Methyl-4-(methylthio)benzaldehyde": "CSc1ccc(C=O)cc1C",
    "Ibuprofen (drug, not an odorant)": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
}
CUSTOM = "Custom (type SMILES below)"
BAR = "#2a78d6"


@st.cache_resource
def get_predictor() -> Predictor:
    return Predictor.load(MODEL_PATH)


def score_chart(scores):
    labels = [l for l, _ in scores][::-1]
    vals = [s for _, s in scores][::-1]
    fig, ax = plt.subplots(figsize=(6, 0.42 * len(scores) + 0.8))
    bars = ax.barh(labels, vals, color=BAR, height=0.7)
    for b, v in zip(bars, vals):
        inside = v > 0.85  # label inside the bar end, otherwise just past it
        ax.text(v - 0.015 if inside else v + 0.015, b.get_y() + b.get_height() / 2,
                f"{v:.2f}", va="center", ha="right" if inside else "left", fontsize=9,
                color="white" if inside else "#0b0b0b")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Model score (not a calibrated probability)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#ecebe7", lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


def on_example_change():
    name = st.session_state["example"]
    if name in EXAMPLES:
        st.session_state["smiles"] = EXAMPLES[name]


def on_smiles_change():
    # Typing a SMILES that is not the selected example switches the dropdown to Custom.
    name = st.session_state.get("example")
    if EXAMPLES.get(name) != st.session_state["smiles"].strip():
        match = [n for n, smi in EXAMPLES.items() if smi == st.session_state["smiles"].strip()]
        st.session_state["example"] = match[0] if match else CUSTOM


def main():
    st.set_page_config(page_title="OdorMap", layout="wide")
    st.title("OdorMap")
    st.caption(SCOPE_NOTE)

    if not MODEL_PATH.exists():
        st.error(f"Model not found at {MODEL_PATH}. Run `python scripts/fetch_data.py` "
                 "and `python scripts/run_baseline.py` first.")
        return
    pred = get_predictor()

    def label(name):
        if name not in EXAMPLES:
            return name
        tag = "in dataset" if pred.is_in_training(EXAMPLES[name]) else "not in dataset"
        return f"{name} — {tag}"

    st.session_state.setdefault("smiles", EXAMPLES["Vanillin"])
    st.selectbox("Example molecule", list(EXAMPLES) + [CUSTOM], key="example",
                 format_func=label, on_change=on_example_change)
    smiles = st.text_input("SMILES", key="smiles", on_change=on_smiles_change).strip()

    if not smiles:
        st.info("Enter a SMILES string or pick an example.")
        return
    if mol_from_smiles(smiles) is None:
        st.error(f"Invalid SMILES: could not parse {smiles!r}. "
                 "Check the string (e.g. vanillin is COc1cc(C=O)ccc1O).")
        return

    result = pred.predict(smiles, top=10)
    if result.in_training:
        st.warning(f"**Training membership: {result.membership}.** This exact molecule "
                   "(ignoring stereochemistry) is in the 4,983-molecule training set, so "
                   "these scores may reflect memorized catalog labels.")
    else:
        st.success(f"**Training membership: {result.membership}.** This molecule is not "
                   "in the training set (exact canonical-SMILES match, stereo ignored); "
                   "close analogs may still be.")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Structure")
        st.image(Draw.MolToImage(mol_from_smiles(smiles), size=(320, 320)),
                 caption=result.canonical)
    with col2:
        st.subheader("Top-10 odor descriptors")
        fig = score_chart(result.scores)
        st.pyplot(fig)
        plt.close(fig)
        st.caption(SCORE_NOTE)


main()
