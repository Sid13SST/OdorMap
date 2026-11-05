"""Generate 2D structure drawings for the static landing page (landing/).

    python scripts/make_landing_assets.py

Writes one SVG per molecule to landing/assets/structures/<slug>.svg, drawn with
RDKit's 2D depiction (rdDepictor + rdMolDraw2D). These are flat 2D structure
diagrams only; no 3D conformers are generated. The molecules and SMILES are the
ones in results/predict_examples.md, so every drawing on the page matches a
recorded prediction. Output is deterministic for a given RDKit version.

Colours follow the app's warm-paper / teal-ink palette (.streamlit/config.toml):
carbon skeleton in ink, heteroatoms in darker tones so labels stay legible on
the paper background. The background is transparent so the page sets it.
"""
from __future__ import annotations

import re
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "landing" / "assets" / "structures"

# Same molecules and SMILES as results/predict_examples.md.
MOLECULES = {
    "vanillin": "COc1cc(C=O)ccc1O",
    "cinnamaldehyde": "O=C/C=C/c1ccccc1",
    "isoamyl-acetate": "CC(=O)OCCC(C)C",
    "geraniol": "CC(C)=CCC/C(C)=C/CO",
    "limonene": "CC1=CCC(CC1)C(=C)C",
    "dimethyl-sulfide": "CSC",
    "isovanillin": "O=Cc1ccc(OC)c(O)c1",
    "5-propylvanillin": "CCCc1cc(C=O)cc(OC)c1O",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
}

INK = (0x1C / 255, 0x21 / 255, 0x27 / 255)       # #1c2127
TEAL = (0x0B / 255, 0x54 / 255, 0x4E / 255)      # #0b544e (oxygen)
SULFUR = (0x5C / 255, 0x3D / 255, 0x00 / 255)    # #5c3d00 (deep amber)
NITROGEN = (0x1F / 255, 0x3A / 255, 0x6B / 255)  # not used by these molecules
SIZE = 360  # viewBox size; the page scales the SVG with CSS


def draw(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit could not parse {smiles!r}")
    rdDepictor.SetPreferCoordGen(True)
    rdDepictor.Compute2DCoords(mol)
    d = rdMolDraw2D.MolDraw2DSVG(SIZE, SIZE)
    o = d.drawOptions()
    o.clearBackground = False
    o.bondLineWidth = 2
    o.padding = 0.12
    o.fixedBondLength = 40
    o.minFontSize = 14
    o.maxFontSize = 20
    o.updateAtomPalette({0: INK, 6: INK, 7: NITROGEN, 8: TEAL, 16: SULFUR})
    d.DrawMolecule(mol)
    d.FinishDrawing()
    svg = d.GetDrawingText()
    # Make the SVG scale with its container: keep the viewBox, drop fixed px size.
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"width='\d+px' height='\d+px' viewBox", "viewBox", svg, count=1)
    return svg


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, smi in MOLECULES.items():
        path = OUT / f"{slug}.svg"
        path.write_text(draw(smi), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
