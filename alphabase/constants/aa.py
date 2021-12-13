# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/constants/aa.ipynb (unless otherwise specified).

__all__ = ['AA_CHEM', 'reset_AA_mass', 'ret_set_AA_df', 'AA_ASCII_MASS', 'AA_DF', 'calc_sequence_mass',
           'calc_AA_masses_for_same_len_seqs', 'calc_sequence_masses_for_same_len_seqs',
           'calc_AA_masses_for_var_len_seqs']

# Cell

import os
import pandas as pd
import numpy as np
from typing import Union, Tuple
from alphabase.yaml_utils import load_yaml

from alphabase.constants.element import calc_mass_from_formula
from alphabase.constants.element import MASS_H2O

AA_CHEM = load_yaml(
    os.path.join(os.path.dirname(__file__),
    'amino_acid.yaml')
)

# Cell

def reset_AA_mass():
    AA_ASCII_MASS = np.ones(128)*1e8
    for aa, chem in AA_CHEM.items():
        AA_ASCII_MASS[ord(aa)] = calc_mass_from_formula(chem)
    return AA_ASCII_MASS

AA_ASCII_MASS = reset_AA_mass()

def ret_set_AA_df():
    AA_DF = pd.DataFrame()
    AA_DF['aa'] = [chr(aa) for aa in range(len(AA_ASCII_MASS))]
    AA_DF['formula'] = ['']*len(AA_ASCII_MASS)
    aa_idxes = []
    formulas = []
    for aa, formula in AA_CHEM.items():
        aa_idxes.append(ord(aa))
        formulas.append(formula)
    AA_DF.loc[aa_idxes, 'formula'] = formulas
    AA_DF['mass'] = AA_ASCII_MASS
    return AA_DF
AA_DF = ret_set_AA_df()


# Cell
def calc_sequence_mass(
    sequence: str
)->np.array:
    '''
    Args:
        sequence (str): unmodified peptide sequence
    Returns:
        np.array: masses of each amino acid.
    '''
    return AA_ASCII_MASS[np.array(sequence,'c').view(np.int8)]

# Cell
def calc_AA_masses_for_same_len_seqs(
    sequence_array: np.array
)->np.array:
    '''
    Calculate AA masses for the array of same-len AA sequences.
    Args:
        sequence_array (np.array): unmodified sequences with the same length.
    Returns:
        np.array: 2-D (array_size, sequence_len) array of masses.
    Raise:
        ValueError: if sequences are not with the same length.
    '''
    return AA_ASCII_MASS[
        # we use np.int32 here because unicode str
        # uses 4 bytes for a char.
        np.array(sequence_array).view(np.int32)
    ].reshape(len(sequence_array), -1)

def calc_sequence_masses_for_same_len_seqs(
    sequence_array: np.array
)->np.array:
    '''
    Calculate sequence masses for the array of same-len AA sequences.
    Args:
        sequence_array (np.array): unmodified sequences with the same length.
    Returns:
        np.array: 1-D (array_size, sequence_len) array of masses.
    Raise:
        ValueError: if sequences are not with the same length.
    '''
    return np.sum(
        calc_AA_masses_for_same_len_seqs(sequence_array),
        axis=1
    )+MASS_H2O


# Cell
def calc_AA_masses_for_var_len_seqs(
    sequence_array: np.array
)->np.array:
    '''
    We recommend to use `calc_AA_masses_for_same_len_seqs` as it is much faster.
    Args:
        sequence_array (np.array): sequences with variable lengths.
    Returns:
        np.array: 1D array of masses, zero values are padded to fill the max length.
    '''
    return AA_ASCII_MASS[
        np.array(sequence_array).view(np.int32)
    ].reshape(len(sequence_array), -1)