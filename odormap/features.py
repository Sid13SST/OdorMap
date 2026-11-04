"""Molecular featurization."""
from __future__ import annotations

from typing import Iterable

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

RADIUS = 2
N_BITS = 2048
_GEN = rdFingerprintGenerator.GetMorganGenerator(radius=RADIUS, fpSize=N_BITS)


def mol_from_smiles(smiles: str):
    """Return an RDKit Mol or None if the SMILES cannot be parsed."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    return Chem.MolFromSmiles(smiles)


def canonical_smiles(smiles: str) -> str | None:
    mol = mol_from_smiles(smiles)
    return None if mol is None else Chem.MolToSmiles(mol)


def morgan_fp(smiles: str) -> np.ndarray:
    """Morgan (ECFP4-like) bit vector, radius 2, 2048 bits, uint8.

    Raises ValueError for unparseable SMILES.
    """
    mol = mol_from_smiles(smiles)
    if mol is None:
        raise ValueError(f"invalid SMILES: {smiles!r}")
    return _GEN.GetFingerprintAsNumPy(mol).astype(np.uint8)


def featurize(smiles_list: Iterable[str]) -> np.ndarray:
    return np.stack([morgan_fp(s) for s in smiles_list])


def murcko_scaffold(smiles: str) -> str:
    """Bemis-Murcko scaffold SMILES ('' for acyclic molecules)."""
    mol = mol_from_smiles(smiles)
    if mol is None:
        raise ValueError(f"invalid SMILES: {smiles!r}")
    return MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
