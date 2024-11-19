import numpy as np
import pandas as pd

from alphabase.psm_reader.keys import PsmDfCols
from alphabase.psm_reader.maxquant_reader import MaxQuantReader
from alphabase.psm_reader.psm_reader import psm_reader_provider, psm_reader_yaml


class SpectronautReader(MaxQuantReader):
    """Reader for Spectronaut's output library TSV/CSV.

    Other parameters, please see `MaxQuantReader`
    in `alphabase.psm_reader.maxquant_reader`

    Parameters
    ----------
    csv_sep : str, optional
        Delimiter for TSV/CSV, by default '\t'
    """

    def __init__(
        self,
        *,
        column_mapping: dict = None,
        modification_mapping: dict = None,
        fdr=0.01,
        keep_decoy=False,
        fixed_C57=False,
        mod_seq_columns=psm_reader_yaml["spectronaut"]["mod_seq_columns"],
        rt_unit="minute",
        **kwargs,
    ):
        super().__init__(
            column_mapping=column_mapping,
            modification_mapping=modification_mapping,
            fdr=fdr,
            keep_decoy=keep_decoy,
            mod_seq_columns=mod_seq_columns,
            fixed_C57=fixed_C57,
            rt_unit=rt_unit,
            **kwargs,
        )

        self.mod_seq_column = "ModifiedPeptide"
        self._min_max_rt_norm = True

    def _init_column_mapping(self):
        self.column_mapping = psm_reader_yaml["spectronaut"]["column_mapping"]

    def _load_file(self, filename):
        self.csv_sep = self._get_table_delimiter(filename)
        df = pd.read_csv(filename, sep=self.csv_sep, keep_default_na=False)
        self._find_mod_seq_column(df)
        if "ReferenceRun" in df.columns:
            df.drop_duplicates(
                ["ReferenceRun", self.mod_seq_column, "PrecursorCharge"], inplace=True
            )
        else:
            df.drop_duplicates([self.mod_seq_column, "PrecursorCharge"], inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df


class SwathReader(SpectronautReader):
    def __init__(
        self,
        *,
        column_mapping: dict = None,
        modification_mapping: dict = None,
        fdr=0.01,
        keep_decoy=False,
        fixed_C57=False,
        mod_seq_columns=psm_reader_yaml["spectronaut"]["mod_seq_columns"],
        **kwargs,
    ):
        """
        SWATH or OpenSWATH library, similar to `SpectronautReader`
        """
        super().__init__(
            column_mapping=column_mapping,
            modification_mapping=modification_mapping,
            fdr=fdr,
            keep_decoy=keep_decoy,
            fixed_C57=fixed_C57,
            mod_seq_columns=mod_seq_columns,
            **kwargs,
        )


class DiannReader(SpectronautReader):
    def __init__(
        self,
        *,
        column_mapping: dict = None,
        modification_mapping: dict = None,
        fdr=0.01,
        keep_decoy=False,
        fixed_C57=False,
        rt_unit="minute",
        **kwargs,
    ):
        """
        Also similar to `MaxQuantReader`,
        but different in column_mapping and modificatin_mapping
        """
        super().__init__(
            column_mapping=column_mapping,
            modification_mapping=modification_mapping,
            fdr=fdr,
            keep_decoy=keep_decoy,
            fixed_C57=fixed_C57,
            rt_unit=rt_unit,
            **kwargs,
        )

        self.mod_seq_column = "Modified.Sequence"
        self._min_max_rt_norm = False

    def _init_column_mapping(self):
        self.column_mapping = psm_reader_yaml["diann"]["column_mapping"]

    def _load_file(self, filename):
        self.csv_sep = self._get_table_delimiter(filename)
        df = pd.read_csv(filename, sep=self.csv_sep, keep_default_na=False)

        return df

    def _post_process(self, origin_df: pd.DataFrame):
        super()._post_process(origin_df)
        self._psm_df.rename(
            columns={PsmDfCols.SPEC_IDX: PsmDfCols.DIANN_SPEC_INDEX}, inplace=True
        )


class SpectronautReportReader(MaxQuantReader):
    """Reader for Spectronaut's report TSV/CSV.

    Other parameters, please see `MaxQuantReader`
    in `alphabase.psm_reader.maxquant_reader`

    Parameters
    ----------
    csv_sep : str, optional
        Delimiter for TSV/CSV, by default ','
    """

    def __init__(
        self,
        *,
        column_mapping: dict = None,
        modification_mapping: dict = None,
        fdr=0.01,
        keep_decoy=False,
        fixed_C57=False,
        rt_unit="minute",
        **kwargs,
    ):
        super().__init__(
            column_mapping=column_mapping,
            modification_mapping=modification_mapping,
            fdr=fdr,
            keep_decoy=keep_decoy,
            fixed_C57=fixed_C57,
            rt_unit=rt_unit,
            **kwargs,
        )

        self.precursor_column = "EG.PrecursorId"

        self._min_max_rt_norm = False

    def _init_column_mapping(self):
        self.column_mapping = psm_reader_yaml["spectronaut_report"]["column_mapping"]

    def _load_file(self, filename):
        self.mod_seq_column = "ModifiedSequence"
        self.csv_sep = self._get_table_delimiter(filename)
        df = pd.read_csv(filename, sep=self.csv_sep, keep_default_na=False)
        df[[self.mod_seq_column, PsmDfCols.CHARGE]] = df[
            self.precursor_column
        ].str.split(".", expand=True, n=2)
        df[PsmDfCols.CHARGE] = df[PsmDfCols.CHARGE].astype(np.int8)
        return df


def register_readers():
    psm_reader_provider.register_reader("spectronaut", SpectronautReader)
    psm_reader_provider.register_reader("speclib_tsv", SpectronautReader)
    psm_reader_provider.register_reader("openswath", SwathReader)
    psm_reader_provider.register_reader("swath", SwathReader)
    psm_reader_provider.register_reader("diann", DiannReader)
    psm_reader_provider.register_reader("spectronaut_report", SpectronautReportReader)
