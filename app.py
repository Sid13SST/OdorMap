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
# Rank gradient in one hue (teal ink): rank 1 darkest, rank 10 lightest. Colour
# encodes rank only; no scent-family grouping is implied. The lightest end keeps
# >=3:1 against the white card so every bar stays visible.
BAR_DARK, BAR_LIGHT = "#0b544e", "#4f9a90"
INK, MUTED, RULE = "#1c2127", "#4a5058", "#e6e3db"
FIRST_RUN = "First run: downloading data and training baseline, ~1 minute…"
EYEBROW = "Odor descriptor model · Leffingwell dataset"

# Presentation only. Selectors target Streamlit's own data-testids and the
# `st-key-<key>` classes Streamlit adds to keyed containers/widgets (checked
# against the installed Streamlit's rendered DOM). No animation is added, so
# there is nothing for prefers-reduced-motion to switch off.
CSS = """
<style>
[data-testid="stMainBlockContainer"] {
  max-width: 1180px; padding-top: 4.5rem; padding-bottom: 3rem;
}
/* Streamlit dims captions with opacity: 0.6 (~3:1 on this background). Use a
   solid muted ink instead so every caption meets WCAG AA (7.5:1). */
[data-testid="stCaptionContainer"] { opacity: 1; color: #4a5058; }
/* Hero */
.st-key-hero { padding-bottom: 1.25rem; margin-bottom: 0.5rem;
  border-bottom: 1px solid #dcd9d0; }
.st-key-hero .om-eyebrow { margin: 0; font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase; color: #0e6b63; }
.st-key-hero h1 { font-size: 2.75rem; line-height: 1.1; letter-spacing: -0.02em;
  padding: 0.2rem 0 0.4rem; }
.st-key-hero [data-testid="stCaptionContainer"] { font-size: 1.05rem;
  line-height: 1.55; color: #4a5058; max-width: 62ch; }
/* Inputs: SMILES reads as code */
.st-key-smiles input { font-family: "Source Code Pro", ui-monospace, monospace;
  font-size: 0.95rem; }
/* Warnings: loud, never buried */
[data-testid="stAlertContentWarning"] { border-left: 4px solid #b7791f;
  padding-left: 0.25rem; }
[data-testid="stAlertContentWarning"] p { font-size: 1rem; line-height: 1.55; }
/* Result cards */
.st-key-structure_card, .st-key-scores_card { background: #ffffff;
  padding: 1.25rem 1.25rem 1.5rem; box-shadow: 0 1px 2px rgba(28, 33, 39, 0.04); }
.st-key-structure_card h3, .st-key-scores_card h3 { font-size: 1.35rem;
  padding-top: 0; }
/* The structure image is drawn at a fixed 320 px; let it shrink inside narrow cards. */
.st-key-structure_card [data-testid="stImageContainer"] { max-width: 100%;
  margin: 0 auto; }
.st-key-structure_card [data-testid="stImageCaption"] p {
  font-family: "Source Code Pro", ui-monospace, monospace; font-size: 0.8rem;
  color: #4a5058; overflow-wrap: anywhere; }
.st-key-scores_card [data-testid="stCaptionContainer"] { color: #4a5058;
  line-height: 1.5; max-width: 75ch; }
/* Footer */
.st-key-footer [data-testid="stCaptionContainer"] { color: #4a5058;
  line-height: 1.6; max-width: 90ch; }
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] { padding-top: 4rem; }
  .st-key-hero h1 { font-size: 2.1rem; }
  .st-key-structure_card, .st-key-scores_card { padding: 1rem; }
}
</style>
"""


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


def _mix(a: str, b: str, t: float) -> tuple[float, float, float]:
    ca = [int(a[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x + (y - x) * t for x, y in zip(ca, cb))


def _luminance(rgb) -> float:
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _label_on(rgb) -> str:
    # White or ink, whichever has the higher WCAG contrast against the bar.
    lum, ink = _luminance(rgb), _luminance(_mix(INK, INK, 0))
    return "white" if 1.05 / (lum + 0.05) >= (lum + 0.05) / (ink + 0.05) else INK


def score_chart(scores):
    labels = [l for l, _ in scores][::-1]
    vals = [s for _, s in scores][::-1]
    n = len(scores)
    # barh draws bottom-up, so bar 0 is rank n (lightest) and the top bar rank 1.
    colors = [_mix(BAR_DARK, BAR_LIGHT, (n - 1 - i) / max(n - 1, 1)) for i in range(n)]
    fig, ax = plt.subplots(figsize=(6, 0.42 * n + 0.8), facecolor="white")
    ax.set_facecolor("white")
    bars = ax.barh(labels, vals, color=colors, height=0.68)
    for b, v, c in zip(bars, vals, colors):
        inside = v > 0.85  # label inside the bar end, otherwise just past it
        ax.text(v - 0.015 if inside else v + 0.015, b.get_y() + b.get_height() / 2,
                f"{v:.2f}", va="center", ha="right" if inside else "left", fontsize=9,
                color=_label_on(c) if inside else INK)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Model score (not a calibrated probability)", color=MUTED, labelpad=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(RULE)
    ax.tick_params(axis="y", length=0, labelsize=10, labelcolor=INK)
    ax.tick_params(axis="x", length=0, labelsize=9, labelcolor=MUTED)
    ax.grid(axis="x", color=RULE, lw=0.8)
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
    with st.container(key="footer"):
        st.caption(ATTRIBUTION)


def main():
    st.set_page_config(page_title="OdorMap", layout="wide")
    st.html(CSS)
    with st.container(key="hero"):
        st.markdown(f'<p class="om-eyebrow">{EYEBROW}</p>', unsafe_allow_html=True)
        st.title("OdorMap", anchor=False)
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
    with col1, st.container(border=True, key="structure_card"):
        st.subheader("Structure")
        # Drawn at 2x and shown at 320 px so bonds and labels stay sharp on HiDPI screens.
        st.image(Draw.MolToImage(mol_from_smiles(smiles), size=(640, 640)), width=320,
                 caption=f"Canonical SMILES: {result.canonical}")
    with col2, st.container(border=True, key="scores_card"):
        st.subheader("Top-10 odor descriptors")
        fig = score_chart(result.scores)
        st.pyplot(fig)
        plt.close(fig)
        st.caption(SCORE_NOTE)
        # Text alternative to the chart image (screen readers, copy/paste).
        with st.expander("Scores as a table"):
            st.dataframe(
                [{"Rank": i, "Descriptor": l, "Score": round(s, 3)}
                 for i, (l, s) in enumerate(result.scores, 1)],
                hide_index=True,
            )


main()
