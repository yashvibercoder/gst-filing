"""
Amazon Reader Module
Reads multiple Amazon GSTR Excel files and consolidates data.
Amazon sheets have 3 summary rows before the header (header is row 4, so header=3).
"""

import pandas as pd
from readers.base_reader import BaseReader


class AmazonReader(BaseReader):

    def _read_sheet(self, file_path, sheet_name):
        """Read an Amazon sheet, skipping the 3 summary rows."""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=3)
            df = df.dropna(how="all")
            return df
        except ValueError:
            # Sheet doesn't exist in this file
            return pd.DataFrame()

    def _extract_gstin(self, file_path):
        """Extract seller GSTIN from Amazon filename."""
        fname = file_path.name if hasattr(file_path, 'name') else str(file_path)
        if "A3SZBDZ05A1P39-" in fname:
            return fname.split("A3SZBDZ05A1P39-")[-1].split(".")[0]
        return fname

    def read_all(self):
        sheets = self.config["amazon_sheets"]
        data = {}

        all_b2c_small = []
        all_b2c_large = []
        all_b2b = []
        all_hsn = []
        all_credit_notes = []

        for file_path in self.file_paths:
            gstin = self._extract_gstin(file_path)
            fname = file_path.name if hasattr(file_path, 'name') else str(file_path)

            # B2C Small
            df = self._read_sheet(file_path, sheets["b2c_small"])
            if len(df) > 0:
                df["source_gstin"] = gstin
                all_b2c_small.append(df)

            # B2C Large
            df = self._read_sheet(file_path, sheets["b2c_large"])
            if len(df) > 0:
                df["source_gstin"] = gstin
                all_b2c_large.append(df)

            # B2B
            df = self._read_sheet(file_path, sheets["b2b"])
            if len(df) > 0:
                df["source_gstin"] = gstin
                all_b2b.append(df)

            # HSN Summary - track source file for empty HSN report
            df = self._read_sheet(file_path, sheets["hsn"])
            if len(df) > 0:
                df["source_file"] = fname
                df["source_gstin"] = gstin
                all_hsn.append(df)

            # Credit Notes (B2B CN / cdnr)
            df = self._read_sheet(file_path, sheets["credit_notes"])
            if len(df) > 0:
                df["source_gstin"] = gstin
                all_credit_notes.append(df)

        # Consolidate across all files
        data["b2c_small"] = pd.concat(all_b2c_small, ignore_index=True) if all_b2c_small else None
        data["b2c_large"] = pd.concat(all_b2c_large, ignore_index=True) if all_b2c_large else None
        data["b2b"] = pd.concat(all_b2b, ignore_index=True) if all_b2b else None
        data["hsn"] = pd.concat(all_hsn, ignore_index=True) if all_hsn else None
        data["credit_notes"] = pd.concat(all_credit_notes, ignore_index=True) if all_credit_notes else None

        for key, df in data.items():
            count = len(df) if df is not None else 0
            print(f"    {key}: {count} rows")

        data["documents"] = None
        data["eco"] = None

        return data
