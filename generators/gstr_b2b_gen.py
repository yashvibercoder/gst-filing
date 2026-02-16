"""
GSTR B2B Template Generator

Source: Amazon B2B + E-Invoice B2B
Output: b2b,sez,de.csv per state

Template columns:
  GSTIN/UIN of Recipient, Receiver Name, Invoice Number, Invoice date,
  Invoice Value, Place Of Supply, Reverse Charge, Applicable % of Tax Rate,
  Invoice Type, E-Commerce GSTIN, Rate, Taxable Value, Cess Amount
"""

import re
import pandas as pd
from processors.rate_normalizer import normalize_rate


def normalize_pos(pos):
    """Normalize Place Of Supply: '23 - Madhya Pradesh' → '23-Madhya Pradesh'."""
    if pd.isna(pos):
        return pos
    return re.sub(r'(\d{2})\s*-\s*', r'\1-', str(pos))

TEMPLATE_COLS = [
    "GSTIN/UIN of Recipient", "Receiver Name", "Invoice Number",
    "Invoice date", "Invoice Value", "Place Of Supply", "Reverse Charge",
    "Applicable % of Tax Rate", "Invoice Type", "E-Commerce GSTIN",
    "Rate", "Taxable Value", "Cess Amount"
]


def map_amazon_b2b(df, state_code):
    """
    Map Amazon B2B to template format.
    Amazon B2B columns are an exact match to the template columns.
    Just filter by state and drop source tracking.
    """
    state_df = df[df["source_gstin"].str[:2] == state_code].copy()
    if len(state_df) == 0:
        return pd.DataFrame(columns=TEMPLATE_COLS)

    # Drop source tracking column
    if "source_gstin" in state_df.columns:
        state_df = state_df.drop(columns=["source_gstin"])

    # Normalize rate (Amazon may have decimal rates like 0.18)
    state_df = normalize_rate(state_df, "Rate")

    # Fill standard defaults
    state_df["Reverse Charge"] = state_df["Reverse Charge"].fillna("N")
    state_df["Invoice Type"] = state_df["Invoice Type"].fillna("Regular B2B")
    state_df["Cess Amount"] = state_df["Cess Amount"].fillna(0)

    return state_df[TEMPLATE_COLS]


def map_einvoice_b2b(df):
    """
    Map E-Invoice B2B (b2b, sez, de sheet) to template format.
    E-Invoice has slight column name differences and extra columns (IRN, taxes).

    E-Invoice columns:
      GSTIN/UIN of Recipient, Receiver Name, Invoice number, Invoice date,
      Invoice value, Place of Supply, Reverse Charge, Applicable % of Tax Rate,
      Invoice Type, E-Commerce GSTIN, Rate, Taxable Value,
      Integrated Tax, Central Tax, State/UT Tax, Cess Amount,
      IRN, IRN date, E-invoice status, ...
    """
    df = df.copy()

    # Fix case differences: E-Invoice uses lowercase in some column names
    df = df.rename(columns={
        "Invoice number": "Invoice Number",
        "Invoice value": "Invoice Value",
        "Place of Supply": "Place Of Supply",
    })

    # Normalize rate
    df = normalize_rate(df, "Rate")

    # Fill defaults
    df["Reverse Charge"] = df["Reverse Charge"].fillna("N")
    df["Invoice Type"] = df["Invoice Type"].fillna("Regular B2B")
    df["Cess Amount"] = df["Cess Amount"].fillna(0)

    # Drop extra E-Invoice columns (IRN, tax breakdowns, status)
    return df[TEMPLATE_COLS]


def generate_b2b_files(amazon_data, einvoice_data, states_dict, folders):
    """
    Generate b2b,sez,de.csv for each state.
    Combines Amazon B2B + E-Invoice B2B.
    Returns dict of {state_code: DataFrame} for use by documents generator.
    """
    amz_b2b = amazon_data.get("b2b")
    b2b_by_state = {}

    for code, info in sorted(states_dict.items()):
        folder = folders[code]
        parts = []

        # Amazon B2B for this seller state
        if amz_b2b is not None and len(amz_b2b) > 0:
            mapped = map_amazon_b2b(amz_b2b, code)
            if len(mapped) > 0:
                parts.append(mapped)

        # E-Invoice B2B for this state
        einv_state = einvoice_data.get(code, {})
        einv_b2b = einv_state.get("b2b")
        if einv_b2b is not None and len(einv_b2b) > 0:
            mapped = map_einvoice_b2b(einv_b2b)
            if len(mapped) > 0:
                parts.append(mapped)

        if not parts:
            continue

        result = pd.concat(parts, ignore_index=True)
        if len(result) == 0:
            continue

        # Normalize Place Of Supply format (strip spaces around dash)
        result["Place Of Supply"] = result["Place Of Supply"].apply(normalize_pos)

        # Deduplicate: keep E-Invoice version (has Receiver Name), drop Amazon dupe
        result = result.sort_values(
            "Receiver Name", key=lambda s: s.fillna("").str.len(),
            ascending=False
        )
        result = result.drop_duplicates(subset=["Invoice Number"], keep="first")
        result = result.reset_index(drop=True)

        b2b_by_state[code] = result

        out_path = folder / "b2b,sez,de.csv"
        result.to_csv(out_path, index=False)
        print(f"  {code}-{info['name']}: b2b,sez,de.csv = {len(result)} rows")

    return b2b_by_state
