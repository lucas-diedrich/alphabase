# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/constants/aa.ipynb (unless otherwise specified).

__all__ = ['reset_AA_mass', 'ret_set_AA_df', 'AA_CHEM', 'AA_ASCII_MASS', 'AA_DF', 'get_sequence_mass',
           'get_AA_masses_for_same_len_seqs', 'get_sequence_masses_for_same_len_seqs', 'get_AA_masses_for_var_len_seqs']

# Cell

import os
import pandas as pd
import numpy as np
from typing import Union, Tuple
from alphabase.yaml_utils import load_yaml

from alphabase.constants.element import calc_formula_mass
from alphabase.constants.element import MASS_H2O

AA_CHEM = load_yaml(
    os.path.join(os.path.dirname(__file__),
    'amino_acid.yaml')
)

def reset_AA_mass():
    AA_ASCII_MASS = np.zeros(128)
    for aa, chem in AA_CHEM.items():
        AA_ASCII_MASS[ord(aa)] = calc_formula_mass(chem)
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
def get_sequence_mass(
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
def get_AA_masses_for_same_len_seqs(
    sequence_array: np.array
)->np.array:
    '''
    Args:
        sequence_array (np.array): unmodified sequences with the same length.
    Returns:
        np.array: 2-D (array_size, sequence_len) array of masses.
    Raise:
        ValueError: if sequences are not with the same length.
    '''
    return AA_ASCII_MASS[
        np.array(sequence_array).view(np.int32)
    ].reshape(len(sequence_array), -1)

def get_sequence_masses_for_same_len_seqs(
    sequence_array: np.array
)->np.array:
    '''
    Args:
        sequence_array (np.array): unmodified sequences with the same length.
    Returns:
        np.array: 1-D (array_size, sequence_len) array of masses.
    Raise:
        ValueError: if sequences are not with the same length.
    '''
    return np.sum(
        get_AA_masses_for_same_len_seqs(sequence_array),
        axis=1
    )+MASS_H2O


# Cell
def get_AA_masses_for_var_len_seqs(
    sequence_array: np.array
)->np.array:
    '''
    We recommend to use `get_AA_masses_for_same_len_seqs` as it is much faster.
    Args:
        sequence_array (np.array): sequences with variable lengths.
    Returns:
        np.array: 1D array of masses, zero values are padded to fill the max length.
    '''
    return AA_ASCII_MASS[
        np.array(sequence_array).view(np.int32)
    ].reshape(len(sequence_array), -1)