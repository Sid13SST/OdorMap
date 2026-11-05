"""OdorMap demo: predict odor descriptors of a single molecule from SMILES.

Run locally (CPU only):
    streamlit run app.py

Uses models/baseline_lr.joblib if present (create with
`python scripts/run_baseline.py`). If it is missing — e.g. on a fresh clone or
a Streamlit Community Cloud deploy, since neither the dataset nor the model is
committed (see DATA.md) — the first run downloads the Leffingwell dataset from
the two pyrfume-data URLs and trains the model once per process
(odormap.train.ensure_model).
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
from odormap import train  # noqa: E402
from odormap.features import mol_from_smiles  # noqa: E402
from odormap.fetch import URLS as DATA_URLS, FetchError  # noqa: E402
from odormap.inference import MODEL_PATH, UNVALIDATED_CAVEAT, Predictor  # noqa: E402

SCOPE_NOTE = ("Scope: predicts catalog odor descriptors of single pure molecules — "
              "not real-world odor sensing, mixtures, or concentration effects.")
SCORE_NOTE = ("Scores are model confidence, not calibrated probabilities: on held-out "
              "scaffolds, molecules scored 0.9–1.0 for a descriptor had it only ~46% of "
              "the time (results/calibration.md).")

# Well-known odorants, all present in the Leffingwell set (stereo-free SMILES match);
# training membership of each is still checked live against the model bundle.
# Type any other SMILES to see the "Not found in training data" path.
EXAMPLES = {
    "Vanillin": "COc1cc(C=O)ccc1O",
    "Cinnamaldehyde": "O=C/C=C/c1ccccc1",
    "Limonene": "CC1=CCC(CC1)C(=C)C",
    "Isoamyl acetate": "CC(=O)OCCC(C)C",
    "Linalool": "CC(C)=CCCC(C)(O)C=C",
    "Eugenol": "COc1cc(CC=C)ccc1O",
    "Ethyl butyrate": "CCCC(=O)OCC",
    "Benzaldehyde": "O=Cc1ccccc1",
}
ATTRIBUTION = (
    "**Data:** Leffingwell Odor Dataset (Sanchez-Lengeling et al. 2019, "
    "[arXiv:1910.10685](https://arxiv.org/abs/1910.10685); original data from John C. "
    "Leffingwell and Associates, PMP 2001 database), "
    "[Zenodo 10.5281/zenodo.4085097](https://doi.org/10.5281/zenodo.4085097), licensed "
    "[CC-BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Molecule and label "
    "tables were joined and a model trained on them; the labels were not modified. "
    "Non-commercial use only."
)
CUSTOM = "Custom (type SMILES below)"
BAR = "#2a78d6"
FIRST_RUN = "First run: downloading data and training baseline, ~1 minute…"


@st.cache_resource(show_spinner=False)
def get_predictor(model_path: str) -> Predictor:
    # Trains (and fetches the data) only if the model file is missing; cached so
    # this happens at most once per process. A failed fetch raises and is not cached.
    return Predictor.load(train.ensure_model(model_path))


def load_predictor() -> Predictor | None:
    if Path(MODEL_PATH).exists():
        return get_predictor(str(MODEL_PATH))
    try:
        with st.spinner(FIRST_RUN):
            return get_predictor(str(MODEL_PATH))
    except FetchError as e:
        st.error(f"Could not download the training data, so the model cannot be "
                 f"trained. {e} The app fetches the dataset at runtime from "
                 f"{' and '.join(DATA_URLS)} (it is not bundled; see DATA.md). "
                 "Check the network connection and reload the page to retry.")
        return None


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


def footer():
    st.divider()
    st.caption(ATTRIBUTION)


def main():
    st.set_page_config(page_title="OdorMap", layout="wide")
    st.title("OdorMap")
    st.caption(SCOPE_NOTE)
    try:
        body()
    finally:
        footer()  # attribution is shown on every path, including errors


def body():
    pred = load_predictor()
    if pred is None:
        return

    def label(name):
        if name not in EXAMPLES:
            return name
        tag = "in dataset" if pred.is_in_training(EXAMPLES[name]) else "not in dataset"
        return f"{name} — {tag}"

    st.session_state.setdefault("smiles", EXAMPLES["Vanillin"])
    pick, entry = st.columns([1, 2])
    with pick:
        st.selectbox("Example molecule", list(EXAMPLES) + [CUSTOM], key="example",
                     format_func=label, on_change=on_example_change,
                     help="Well-known odorants. Picking one fills in its SMILES.")
    with entry:
        smiles = st.text_input(
            "SMILES", key="smiles", on_change=on_smiles_change,
            placeholder="e.g. COc1cc(C=O)ccc1O",
            help="A single molecule as a SMILES string. Press Enter to predict.",
        ).strip()

    if not smiles:
        st.info("Enter a SMILES string or pick an example.")
        return
    if mol_from_smiles(smiles) is None:
        st.error(f"Invalid SMILES: could not parse {smiles!r}. "
                 "Check the string (e.g. vanillin is COc1cc(C=O)ccc1O).")
        return

    with st.spinner("Scoring odor descriptors…"):
        result = pred.predict(smiles, top=10)
    if result.in_training:
        st.warning(f"**Training membership: {result.membership}.** This exact molecule "
                   "(ignoring stereochemistry) is in the 3,522-molecule Leffingwell training "
                   "set, so these scores may reflect memorized catalog labels.")
    else:
        st.warning(f"**Training membership: {result.membership}** (exact canonical-SMILES "
                   f"match, stereo ignored). {UNVALIDATED_CAVEAT}")

    col1, col2 = st.columns([1, 2])
    with col1, st.container(border=True):
        st.subheader("Structure")
        # Drawn at 2x and shown at 320 px so bonds and labels stay sharp on HiDPI screens.
        st.image(Draw.MolToImage(mol_from_smiles(smiles), size=(640, 640)), width=320,
                 caption=f"Canonical SMILES: {result.canonical}")
    with col2, st.container(border=True):
        st.subheader("Top-10 odor descriptors")
        fig = score_chart(result.scores)
        st.pyplot(fig)
        plt.close(fig)
        st.caption(SCORE_NOTE)


main()
