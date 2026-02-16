"""
ECO Template Generator

Source: Flipkart Section 3 (GSTR-8)
Output: eco.csv per state

Template columns:
  Nature of Supply, GSTIN of E-Commerce Operator, E-Commerce Operator Name,
  Net value of supplies, Integrated tax, Central tax, State/UT tax, Cess
"""

import pandas as pd
from processors.state_detector import filter_by_gstin

TEMPLATE_COLS = [
    "Nature of Supply", "GSTIN of E-Commerce Operator",
    "E-Commerce Operator Name", "Net value of supplies",
    "Integrated tax", "Central tax", "State/UT tax", "Cess"
]


def map_flipkart_eco(df):
    """Map Flipkart Section 3 (GSTR-8) columns to ECO template format."""
    df = df.copy()
    df = df.rename(columns={
        "GSTIN of Flipkart.Com": "GSTIN of E-Commerce Operator",
        "Net Taxable Value": "Net value of supplies",
        "IGST Amount Rs.": "Integrated tax",
        "CGST Amount Rs.": "Central tax",
        "SGST Amount Rs.": "State/UT tax",
    })
    df["Nature of Supply"] = "Liable to collect tax u/s 52(TCS)"
    df["E-Commerce Operator Name"] = ""
    df["Cess"] = ""
    # Drop extra columns
    for col in ["GSTIN", "Seller ID issued by Flipkart.Com",
                "Gross Taxable Value Rs.", "Taxable Sales Return Value Rs.",
                "TCS %", "TCS IGST amount Rs.", "TCS CGST amount Rs.",
                "TCS SGST amount Rs.", "Invoice Qty\n(Net)"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    return df[TEMPLATE_COLS]


def generate_eco_files(flipkart_data, states_dict, folders):
    """
    Generate eco.csv for each state that has Flipkart ECO data.
    """
    fk_eco = flipkart_data.get("eco")
    if fk_eco is None or len(fk_eco) == 0:
        return

    for code, info in sorted(states_dict.items()):
        gstin = info["gstin"]

        # Filter Flipkart ECO for this seller state
        state_eco = filter_by_gstin(fk_eco, "GSTIN", gstin)
        if len(state_eco) == 0:
            continue

        result = map_flipkart_eco(state_eco)
        if len(result) == 0:
            continue

        out_path = folders[code] / "eco.csv"
        result.to_csv(out_path, index=False)
        print(f"  {code}-{info['name']}: eco.csv = {len(result)} rows")
