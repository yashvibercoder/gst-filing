"""
Meesho Reader Module
Reads Meesho GST report Excel file.
Only sheet "80307" (raw transaction data) is used.
"""

import pandas as pd
from readers.base_reader import BaseReader


class MeeshoReader(BaseReader):

    def read_all(self):
        sheets = self.config["meesho_sheets"]
        file_path = self.file_paths[0]
        data = {}

        # Raw transaction data from sheet "80307"
        df = pd.read_excel(file_path, sheet_name=sheets["raw_data"])
        df = df.dropna(how="all")
        data["raw"] = df
        print(f"    Raw transactions: {len(df)} rows")

        sales = df[df["quantity"] > 0]
        returns = df[df["quantity"] <= 0]
        print(f"    Sales: {len(sales)}, Returns: {len(returns)}")

        data["b2b"] = None
        data["documents"] = None
        data["credit_notes"] = None

        return data
