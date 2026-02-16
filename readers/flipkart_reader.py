"""
Flipkart Reader Module
Reads Flipkart GST export Excel file.
Row 1 is the header in all Flipkart sheets (no summary rows).
"""

import pandas as pd
from readers.base_reader import BaseReader


class FlipkartReader(BaseReader):

    def read_all(self):
        sheets = self.config["flipkart_sheets"]
        file_path = self.file_paths[0]
        data = {}

        # B2C intrastate - Section 7(A)(2)
        # Cols: GSTIN, Gross Taxable Value Rs., Taxable Sales Return Value Rs.,
        #       Aggregate Taxable Value Rs., CGST %, CGST Amount Rs.,
        #       SGST/UT %, SGST /UT Amount Rs., Cess %, CESS Amount Rs.
        df_intra = pd.read_excel(file_path, sheet_name=sheets["b2c_intrastate"])
        df_intra = df_intra.dropna(how="all")
        data["b2c_intra"] = df_intra
        print(f"    B2C intrastate: {len(df_intra)} rows")

        # B2C interstate - Section 7(B)(2)
        # Cols: GSTIN, Gross Taxable Value Rs., Taxable Sales Return Value Rs.,
        #       Aggregate Taxable Value Rs., IGST %, IGST Amount Rs.,
        #       Cess %, CESS Amount Rs., Delivered State (PoS), Delivered State Code
        df_inter = pd.read_excel(file_path, sheet_name=sheets["b2c_interstate"])
        df_inter = df_inter.dropna(how="all")
        data["b2c_inter"] = df_inter
        print(f"    B2C interstate: {len(df_inter)} rows")

        # HSN - Section 12
        # Cols: GSTIN, HSN Number, Total Quantity in Nos., Total Value Rs.,
        #       Total Taxable Value Rs., IGST Amount Rs., CGST Amount Rs.,
        #       SGST Amount Rs., Cess Rs.
        df_hsn = pd.read_excel(file_path, sheet_name=sheets["hsn"])
        df_hsn = df_hsn.dropna(how="all")
        data["hsn"] = df_hsn
        print(f"    HSN: {len(df_hsn)} rows")

        # Documents - Section 13
        # Cols: GSTIN, Invoice Series From, Invoice Series To,
        #       Total Number of Invoices, Cancelled if any, Net invoices Issued
        df_docs = pd.read_excel(file_path, sheet_name=sheets["documents"])
        df_docs = df_docs.dropna(how="all")
        data["documents"] = df_docs
        print(f"    Documents: {len(df_docs)} rows")

        # ECO - Section 3 in GSTR-8
        # Cols: GSTIN, Seller ID, Flipkart GSTIN, Gross Taxable Value,
        #       Taxable Sales Return, Net Taxable Value, TCS %,
        #       TCS IGST, TCS CGST, TCS SGST, IGST, CGST, SGST, Invoice Qty
        df_eco = pd.read_excel(file_path, sheet_name=sheets["eco"])
        df_eco = df_eco.dropna(how="all")
        data["eco"] = df_eco
        print(f"    ECO: {len(df_eco)} rows")

        data["b2b"] = None
        data["credit_notes"] = None

        return data
