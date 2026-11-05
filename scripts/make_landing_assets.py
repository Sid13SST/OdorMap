"""Generate 2D structure drawings for the static landing page (landing/).

    python scripts/make_landing_assets.py

Writes one SVG per molecule to landing/assets/structures/<slug>.svg, drawn with
RDKit's 2D depiction (rdDepictor + rdMolDraw2D). These are flat 2D structure
diagrams only; no 3D conformers are generated. The molecules and SMILES are the
ones in results/predict_examples.md, so every drawing on the page matches a
recorded prediction. Output is deterministic for a given RDKit version.

Colours are light-on-dark for the page's dark theme: the carbon skeleton in the
page's luminous teal accent, heteroatom labels in near-white / pale grey so they
stay legible on the dark card. The background is transparent so the page sets
it. Each drawing also carries data-atoms on its root <svg>: the x,y drawing
coordinates of every atom in SMILES order, read from the same RDKit drawing,
which the page uses to highlight atoms and bond neighbourhoods.
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

TEAL = (0x5E / 255, 0xE6 / 255, 0xD6 / 255)      # #5ee6d6 (carbon skeleton)
OXYGEN = (0xEE / 255, 0xF4 / 255, 0xF5 / 255)    # #eef4f5 (near-white)
SULFUR = (0xC4 / 255, 0xD0 / 255, 0xD6 / 255)    # #c4d0d6 (pale grey)
NITROGEN = (0xB4 / 255, 0xC8 / 255, 0xF0 / 255)  # not used by these molecules
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
    o.updateAtomPalette({0: TEAL, 6: TEAL, 7: NITROGEN, 8: OXYGEN, 16: SULFUR})
    d.DrawMolecule(mol)
    d.FinishDrawing()
    svg = d.GetDrawingText()
    # Make the SVG scale with its container: keep the viewBox, drop fixed px size.
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"width='\d+px' height='\d+px' viewBox", "viewBox", svg, count=1)
    atoms = ";".join(
        f"{d.GetDrawCoords(i).x:.1f},{d.GetDrawCoords(i).y:.1f}" for i in range(mol.GetNumAtoms())
    )
    svg = svg.replace("viewBox=", f"data-atoms='{atoms}' viewBox=", 1)
    return svg


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, smi in MOLECULES.items():
        path = OUT / f"{slug}.svg"
        path.write_text(draw(smi), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
