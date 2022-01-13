# AUTOGENERATED! DO NOT EDIT! File to edit: nbdev_nbs/spectrum_library/library_base.ipynb (unless otherwise specified).

__all__ = ['SpecLibBase']

# Cell
import pandas as pd
import numpy as np
import typing

import alphabase.peptide.fragment as fragment
from ..io.hdf import HDF_File

class SpecLibBase(object):
    def __init__(self,
        # ['b_z1','b_z2','y_z1','y_modloss_z1', ...];
        # 'b_z1': 'b' is the fragment type and
        # 'z1' is the charge state z=1.
        charged_frag_types:typing.List[str],
        min_precursor_mz = 400, max_precursor_mz = 6000,
        min_frag_mz = 200, max_frag_mz = 2000,
    ):
        self.charged_frag_types = charged_frag_types
        self._precursor_df = pd.DataFrame()
        self._fragment_intensity_df = pd.DataFrame()
        self._fragment_mz_df = pd.DataFrame()
        self.min_frag_mz = min_frag_mz
        self.max_frag_mz = max_frag_mz
        self.min_precursor_mz = min_precursor_mz
        self.max_precursor_mz = max_precursor_mz

    @property
    def precursor_df(self):
        return self._precursor_df

    @property
    def fragment_mz_df(self):
        return self._fragment_mz_df

    @property
    def fragment_intensity_df(self):
        return self._fragment_intensity_df

    def clip_by_precursor_mz_(self):
        '''
        Clip self._precursor_df inplace
        '''
        self._precursor_df.drop(
            self._precursor_df.loc[
                (self._precursor_df['precursor_mz']<self.min_precursor_mz)|
                (self._precursor_df['precursor_mz']>self.max_precursor_mz)
            ].index, inplace=True
        )
        self._precursor_df.reset_index(drop=True, inplace=True)

    def mask_fragment_intensity_by_mz_(self):
        '''
        Clip self._fragment_intensity_df inplace.
        All clipped intensities are set as zeros.
        A more generic way is to use a mask.
        '''
        self._fragment_intensity_df[
            (self._fragment_mz_df<self.min_frag_mz)|
            (self._fragment_mz_df>self.max_frag_mz)
        ] = 0

    def load_fragment_df(self, **kwargs):
        self._precursor_df.sort_values('nAA', inplace=True)
        self.calc_fragment_mz_df(**kwargs)
        self.load_fragment_intensity_df(**kwargs)
        for col in self._fragment_mz_df.columns.values:
            if 'modloss' in col:
                self._fragment_intensity_df.loc[
                    self._fragment_mz_df[col]==0,col
                ] = 0

    def flatten_fragment_data(
        self
    )->typing.Tuple[np.array, np.array]:
        '''
        Create flattened (1-D) np.array for fragment mz and intensity
        dataframes, respectively. The arrays are references to
        original data, that means:
          1. This method is fast;
          2. Changing the array values will change the df values.
        They can be unraveled back using:
          `array.reshape(len(self._fragment_mz_df.columns), -1)`

        Returns:
            np.array: 1-D flattened mz array (a reference to
            original fragment mz df data)
            np.array: 1-D flattened intensity array (a reference to
            original fragment intensity df data)
        '''
        return (
            self._fragment_mz_df.values.reshape(-1),
            self._fragment_intensity_df.values.reshape(-1)
        )

    def load_fragment_intensity_df(self, **kwargs):
        '''
        All sub-class must re-implement this method.
        Fragment intensities can be predicted or from AlphaPept, or ...
        '''
        raise NotImplementedError(
            f'Sub-class of "{self.__class__}" must re-implement "load_fragment_intensity_df()"'
        )

    def calc_fragment_mz_df(self):
        if 'frag_start_idx' in self._precursor_df.columns:
            del self._precursor_df['frag_start_idx']
            del self._precursor_df['frag_end_idx']

        (
            self._precursor_df, self._fragment_mz_df
        ) = fragment.create_fragment_mz_dataframe(
            self._precursor_df, self.charged_frag_types
        )

    def calc_precursor_mz(self):
        fragment.update_precursor_mz(self._precursor_df)
        self.clip_by_precursor_mz_()

    def update_precursor_mz(self):
        self.calc_precursor_mz()

    def save_hdf(self, hdf_file):
        _hdf = HDF_File(
            hdf_file,
            read_only=False,
            truncate=True,
            delete_existing=True
        )
        _hdf.library = {
            'precursor_df': self._precursor_df,
            'fragment_mz_df': self._fragment_mz_df,
            'fragment_intensity_df': self._fragment_intensity_df,
        }

    def load_hdf(self, hdf_file):
        _hdf = HDF_File(
            hdf_file,
        )
        self._precursor_df = _hdf.library.precursor_df.values
        self._fragment_mz_df = _hdf.library.fragment_mz_df.values
        self._fragment_intensity_df = _hdf.library.fragment_intensity_df.values