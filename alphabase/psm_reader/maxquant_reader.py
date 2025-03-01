import copy
import warnings
from typing import Optional

import numba
import numpy as np
import pandas as pd

from alphabase.constants.modification import MOD_DF
from alphabase.psm_reader.keys import PsmDfCols
from alphabase.psm_reader.psm_reader import (
    PSMReaderBase,
    psm_reader_provider,
    psm_reader_yaml,
)

# make sure all warnings are shown
warnings.filterwarnings("always")

mod_to_unimod_dict = {}
for mod_name, unimod_id in MOD_DF[["mod_name", "unimod_id"]].values:
    unimod_id = int(unimod_id)
    if unimod_id == -1 or unimod_id == "-1":
        continue
    if mod_name[-2] == "@":
        mod_to_unimod_dict[mod_name] = f"{mod_name[-1]}(UniMod:{unimod_id})"
    else:
        mod_to_unimod_dict[mod_name] = f"_(UniMod:{unimod_id})"


@numba.njit
def replace_parentheses_with_brackets(
    modseq: str,
):
    mod_depth = 0
    for i, aa in enumerate(modseq):
        if aa == "(":
            if mod_depth <= 0:
                modseq = modseq[:i] + "[" + modseq[i + 1 :]
            mod_depth += 1
        elif aa == "[":
            mod_depth += 1
        elif aa == ")":
            mod_depth -= 1
            if mod_depth <= 0:
                modseq = modseq[:i] + "]" + modseq[i + 1 :]
        elif aa == "]":
            mod_depth -= 1
    return modseq


@numba.njit
def parse_mod_seq(
    modseq: str,
    mod_sep: str = "()",
    fixed_C57: bool = True,
) -> tuple:
    """Extract modifications and sites from the modified sequence (modseq)

    Parameters
    ----------
    modseq : str
        modified sequence to extract modifications.

    mod_sep : str, optional
        separator to indicate the modification section.
        Defaults to '()'

    fixed_C : bool
        If Carbamidomethyl@C is a fixed modification
        and not displayed in the sequence. Defaults to True for MaxQuant.

    Returns
    -------
    tuple
        str: naked peptide sequence

        str: modification names, separated by ';'

        str: modification sites, separated by ';'.
        0 for N-term; -1 for C-term; 1 to N for normal modifications.
    """
    PeptideModSeq = modseq
    underscore_for_ncterm = modseq[0] == "_"
    mod_list = []
    site_list = []
    site = PeptideModSeq.find(mod_sep[0])
    while site != -1:
        site_end = PeptideModSeq.find(mod_sep[1], site + 1) + 1
        if site_end < len(PeptideModSeq) and PeptideModSeq[site_end] == mod_sep[1]:
            site_end += 1
        if underscore_for_ncterm:
            site_list.append(site - 1)
        else:
            site_list.append(site)
        start_mod = site
        if start_mod > 0:
            start_mod -= 1
        mod_list.append(PeptideModSeq[start_mod:site_end])
        PeptideModSeq = PeptideModSeq[:site] + PeptideModSeq[site_end:]
        site = PeptideModSeq.find(mod_sep[0], site)

    # patch for phos. How many other modification formats does MQ have?
    site = PeptideModSeq.find("p")
    while site != -1:
        mod_list.append(PeptideModSeq[site : site + 2])
        site_list = [i - 1 if i > site else i for i in site_list]
        if underscore_for_ncterm:
            site_list.append(site)
        else:
            site_list.append(site + 1)
        PeptideModSeq = PeptideModSeq[:site] + PeptideModSeq[site + 1 :]
        site = PeptideModSeq.find("p", site)

    if fixed_C57:
        site = PeptideModSeq.find("C")
        while site != -1:
            if underscore_for_ncterm:
                site_list.append(site)
            else:
                site_list.append(site + 1)
            mod_list.append("C" + "Carbamidomethyl (C)".join(mod_sep))
            site = PeptideModSeq.find("C", site + 1)
    sequence = PeptideModSeq.strip("_")
    nAA = len(sequence)
    return (
        sequence,
        ";".join(mod_list),
        ";".join([str(i) if i <= nAA else "-1" for i in site_list]),
    )


class MaxQuantReader(PSMReaderBase):
    def __init__(
        self,
        *,
        column_mapping: dict = None,
        modification_mapping: dict = None,
        fdr=0.01,
        keep_decoy=False,
        fixed_C57=True,
        mod_seq_columns=None,
        **kwargs,
    ):
        """Reader for MaxQuant msms.txt and evidence.txt

        Parameters
        ----------
        column_mapping : dict, optional
            By default None. If None, use
            `psm_reader_yaml['maxquant']['column_mapping']`
            (alphabase.psm_reader.psm_reader_yaml).

        modification_mapping : dict, optional
            By default None. If None, use
            `psm_reader_yaml['maxquant']['modification_mapping']`
            (alphabase.psm_reader.psm_reader_yaml).

        fdr : float, optional
            Load PSMs with FDR < this fdr, by default 0.01

        keep_decoy : bool, optional
            If keep decoy PSMs, by default False

        fixed_C57 : bool, optional
            If true, the search engine will not show `Carbamidomethyl`
            in the modified sequences.
            by default True

        mod_seq_columns : list, optional
            The columns to find modified sequences,
            by default ['Modified sequence']
        """
        if mod_seq_columns is None:
            mod_seq_columns = ["Modified sequence"]
        super().__init__(
            column_mapping=column_mapping,
            modification_mapping=modification_mapping,
            fdr=fdr,
            keep_decoy=keep_decoy,
            **kwargs,
        )

        self.fixed_C57 = fixed_C57
        self._mod_seq_columns = mod_seq_columns
        self.mod_seq_column = "Modified sequence"

    def _find_mod_seq_column(self, df):
        for mod_seq_col in self._mod_seq_columns:
            if mod_seq_col in df.columns:
                self.mod_seq_column = mod_seq_col
                break

    def _init_modification_mapping(self):
        self.modification_mapping = copy.deepcopy(
            # otherwise maxquant reader will modify the dict inplace
            psm_reader_yaml["maxquant"]["modification_mapping"]
        )

    def set_modification_mapping(self, modification_mapping: Optional[dict] = None):
        super().set_modification_mapping(modification_mapping)
        self._add_all_unimod()
        self._extend_mod_brackets()
        self._reverse_mod_mapping()

    def _add_all_unimod(self):
        for mod_name, unimod in mod_to_unimod_dict.items():
            if mod_name in self.modification_mapping:
                self.modification_mapping[mod_name].append(unimod)
            else:
                self.modification_mapping[mod_name] = [unimod]

    def _extend_mod_brackets(self):
        """update modification_mapping to include different bracket types."""

        for key, mod_list in list(self.modification_mapping.items()):
            mod_set = set(mod_list)
            # extend bracket types of modifications
            # K(Acetyl) -> K[Acetyl]
            # (Phospho) -> _(Phospho)
            # _[Phospho] -> _(Phospho)
            for mod in mod_list:
                if mod[1] == "(":
                    mod_set.add(f"{mod[0]}[{mod[2:-1]}]")
                elif mod[1] == "[":
                    mod_set.add(f"{mod[0]}({mod[2:-1]})")

                if mod.startswith("_"):
                    mod_set.add(f"{mod[1:]}")
                elif mod.startswith("("):
                    mod_set.add(f"_{mod}")
                    mod_set.add(f"[{mod[1:-1]}]")
                    mod_set.add(f"_[{mod[1:-1]}]")
                elif mod.startswith("["):
                    mod_set.add(f"_{mod}")
                    mod_set.add(f"({mod[1:-1]})")
                    mod_set.add(f"_({mod[1:-1]})")

            self.modification_mapping[key] = list(mod_set)

    def _translate_decoy(self, origin_df=None):
        if PsmDfCols.DECOY in self._psm_df.columns:
            self._psm_df[PsmDfCols.DECOY] = (
                self._psm_df[PsmDfCols.DECOY] == "-"
            ).astype(np.int8)

    def _init_column_mapping(self):
        self.column_mapping = psm_reader_yaml["maxquant"]["column_mapping"]

    def _load_file(self, filename):
        csv_sep = self._get_table_delimiter(filename)
        df = pd.read_csv(filename, sep=csv_sep, keep_default_na=False)
        self._find_mod_seq_column(df)
        df = df[~pd.isna(df["Retention time"])]
        df.fillna("", inplace=True)

        # remove MBR PSMs as they are currently not supported and will crash import
        mapped_columns = self._find_mapped_columns(df)
        if PsmDfCols.SCAN_NUM in mapped_columns:
            scan_num_col = mapped_columns[PsmDfCols.SCAN_NUM]
            no_ms2_mask = df[scan_num_col] == ""
            if (num_no_ms2_mask := np.sum(no_ms2_mask)) > 0:
                warnings.warn(
                    f"MaxQuant PSM file contains {num_no_ms2_mask} MBR PSMs without MS2 scan. This is not yet supported and rows containing MBR PSMs will be removed."
                )
                df = df[~no_ms2_mask]
                df.reset_index(drop=True, inplace=True)
            df[scan_num_col] = df[scan_num_col].astype(int)

        # if 'K0' in df.columns:
        #     df['Mobility'] = df['K0'] # Bug in MaxQuant? It should be 1/K0
        # min_rt = df['Retention time'].min()
        return df

    def _load_modifications(self, origin_df: pd.DataFrame):
        if origin_df[self.mod_seq_column].str.contains("[", regex=False).any():
            if origin_df[self.mod_seq_column].str.contains("(", regex=False).any():
                origin_df[self.mod_seq_column] = origin_df[self.mod_seq_column].apply(
                    replace_parentheses_with_brackets
                )
            mod_sep = "[]"
        else:
            mod_sep = "()"

        (seqs, self._psm_df[PsmDfCols.MODS], self._psm_df[PsmDfCols.MOD_SITES]) = zip(
            *origin_df[self.mod_seq_column].apply(
                parse_mod_seq,
                mod_sep=mod_sep,
                fixed_C57=self.fixed_C57,
            )
        )
        if PsmDfCols.SEQUENCE not in self._psm_df.columns:
            self._psm_df[PsmDfCols.SEQUENCE] = seqs


def register_readers():
    psm_reader_provider.register_reader("maxquant", MaxQuantReader)
