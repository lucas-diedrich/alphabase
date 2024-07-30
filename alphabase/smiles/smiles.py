from typing import Optional

import pandas as pd
from rdkit import Chem
from rdkit.Chem.rdmolops import ReplaceSubstructs, SanitizeMol

from alphabase.constants.aa import AA_Formula
from alphabase.constants.modification import MOD_DF

N_TERM_PLACEHOLDER = "[Xe]"
C_TERM_PLACEHOLDER = "[Rn]"

MOD_DF_SMILES = MOD_DF[MOD_DF["smiles"] != ""]

aa_smiles = {
    aa: AA_Formula.loc[aa]["smiles"]
    for aa in AA_Formula.index
    if not pd.isna(AA_Formula.loc[aa]["smiles"])
}
aa_mols = {aa: Chem.MolFromSmiles(aa_smiles[aa]) for aa in aa_smiles}

n_term_modifications = {
    name: smiles
    for name, smiles in zip(MOD_DF_SMILES["mod_name"], MOD_DF_SMILES["smiles"])
    if "@Protein_N-term" in name or "@Any_N-term" in name
}
c_term_modifications = {
    name: smiles
    for name, smiles in zip(MOD_DF_SMILES["mod_name"], MOD_DF_SMILES["smiles"])
    if "@Protein_C-term" in name or "@Any_C-term" in name
}
ptm_dict = {
    name: smiles
    for name, smiles in zip(MOD_DF_SMILES["mod_name"], MOD_DF_SMILES["smiles"])
    if name not in n_term_modifications and name not in c_term_modifications
}


def validate_correct_args(
    aa_smiles: str, n_term_mod: Optional[str] = None, c_term_mod: Optional[str] = None
) -> None:
    """
    Validate the amino acid, N-terminal modification, and C-terminal modification.

    Args:
        aa_smiles (str): SMILES of an amino acid with or without PTMs, has to have the placeholder atoms [Xe] for N-term and [Rn] for C-term.
        n_term_mod (Optional[str]): N-terminal modification name. Options are the keys in the n_term_modifications dict.
        c_term_mod (Optional[str]): C-terminal modification name. Options are the keys in the c_term_modifications dict.

    Raises:
        ValueError: If the amino acid is invalid, or if N-terminal / C-terminal modification is not recognized.
    """
    if N_TERM_PLACEHOLDER not in aa_smiles or C_TERM_PLACEHOLDER not in aa_smiles:
        raise ValueError(
            f"The amino acid {aa_smiles} must contain the N-terminal and C-terminal placeholders in order to be modified."
        )
    if n_term_mod is not None and n_term_mod not in n_term_modifications:
        raise ValueError(f"Unrecognized N-terminal modification: {n_term_mod}")
    if c_term_mod is not None and c_term_mod not in c_term_modifications:
        raise ValueError(f"Unrecognized C-terminal modification: {c_term_mod}")
    _mol = Chem.MolFromSmiles(aa_smiles)
    if _mol is None:
        raise ValueError(f"Invalid amino acid SMILES: {aa_smiles}")


def modify_amino_acid(
    aa_smiles: str, n_term_mod: Optional[str] = None, c_term_mod: Optional[str] = None
) -> str:
    """
    Modify an amino acid with N-terminal and C-terminal modifications.

    Args:
        aa (str): SMILES of an amino acid with or without PTMs, has to have the placeholder atoms [Xe] for N-term and [Rn] for C-term.
        n_term_mod (Optional[str]): N-terminal modification name. Options are the keys in the n_term_modifications dict. If None, the amino acid is not modified, so using hydrogen atoms.
        c_term_mod (Optional[str]): C-terminal modification name. Options are the keys in the c_term_modifications dict. If None, the amino acid is not modified, so using the -OH group.

    Returns:
        str: SMILES string of the modified amino acid.
    """
    validate_correct_args(aa_smiles, n_term_mod, c_term_mod)
    mol = Chem.MolFromSmiles(aa_smiles)
    n_term_placeholder_mol = Chem.MolFromSmiles(N_TERM_PLACEHOLDER, sanitize=False)
    c_term_placeholder_mol = Chem.MolFromSmiles(C_TERM_PLACEHOLDER, sanitize=False)

    # Apply N-terminal modification
    if n_term_mod:
        n_mod_smiles = n_term_modifications[n_term_mod]
        n_mod_mol = Chem.MolFromSmiles(n_mod_smiles)
        mol = ReplaceSubstructs(mol, n_term_placeholder_mol, n_mod_mol)[0]

        if "Dimethyl" in n_term_mod:
            mol = ReplaceSubstructs(mol, n_term_placeholder_mol, n_mod_mol)[0]
        else:
            mol = ReplaceSubstructs(
                mol, n_term_placeholder_mol, Chem.MolFromSmiles("[H]", sanitize=False)
            )[0]
    else:
        mol = ReplaceSubstructs(
            mol,
            n_term_placeholder_mol,
            Chem.MolFromSmiles("[H]", sanitize=False),
            replaceAll=True,
        )[0]

    # Apply C-terminal modification
    if c_term_mod:
        c_mod_smiles = c_term_modifications[c_term_mod]
        c_mod_mol = Chem.MolFromSmiles(c_mod_smiles)
        mol = ReplaceSubstructs(mol, c_term_placeholder_mol, c_mod_mol)[0]
    else:
        mol = ReplaceSubstructs(
            mol, c_term_placeholder_mol, Chem.MolFromSmiles("O", sanitize=False)
        )[0]

    SanitizeMol(mol)
    return Chem.MolToSmiles(mol)
