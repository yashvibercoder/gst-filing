"""
E-Invoice Reader Module
Reads one or more E-Invoice files (EINV_<GSTIN>_<YEAR>.xlsx).
Sheets have 3 metadata rows before the header (header=3).
Returns data keyed by state code for dynamic multi-state support.
"""

import pandas as pd
from pathlib import Path
from readers.base_reader import BaseReader


class EInvoiceReader(BaseReader):

    def _read_sheet(self, file_path, sheet_name):
        """Read an E-Invoice sheet, skipping the 3 metadata rows."""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=3)
            df = df.dropna(how="all")
            return df
        except ValueError:
            return pd.DataFrame()

    def _extract_gstin(self, file_path):
        """Extract GSTIN from filename: EINV_<GSTIN>_<YEAR>.xlsx"""
        fname = file_path.name if hasattr(file_path, 'name') else Path(file_path).name
        parts = fname.replace('.xlsx', '').split('_')
        if len(parts) >= 2:
            return parts[1]
        return None

    def read_all(self):
        """
        Read all E-Invoice files, keyed by state code.
        Returns: {"07": {"b2b": df, "credit_notes": df, "hsn_b2b": df}, ...}
        """
        sheets = self.config["einvoice_sheets"]
        data_by_state = {}

        for file_path in self.file_paths:
            gstin = self._extract_gstin(file_path)
            if not gstin:
                print(f"    WARNING: Could not extract GSTIN from {file_path}")
                continue

            state_code = gstin[:2]
            fname = file_path.name if hasattr(file_path, 'name') else str(file_path)
            print(f"    E-Invoice {fname} (state {state_code}):")

            file_data = {}

            # B2B invoices
            df_b2b = self._read_sheet(file_path, sheets["b2b"])
            file_data["b2b"] = df_b2b if len(df_b2b) > 0 else None
            print(f"      B2B: {len(df_b2b)} rows")

            # Credit/Debit notes
            df_cn = self._read_sheet(file_path, sheets["credit_notes"])
            file_data["credit_notes"] = df_cn if len(df_cn) > 0 else None
            print(f"      Credit notes: {len(df_cn)} rows")

            # HSN B2B
            df_hsn = self._read_sheet(file_path, sheets["hsn_b2b"])
            file_data["hsn_b2b"] = df_hsn if len(df_hsn) > 0 else None
            print(f"      HSN B2B: {len(df_hsn)} rows")

            data_by_state[state_code] = file_data

        return data_by_state
