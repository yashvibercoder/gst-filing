"""
Credit Notes Template Generator

Source: Amazon B2B CN (cdnr) + E-Invoice CDNR
Output: cdnr1.csv per state

Template columns:
  GSTIN/UIN of Recipient, Receiver Name, Note Number, Note Date,
  Note Type, Place Of Supply, Reverse Charge, Note Supply Type,
  Note Value, Applicable % of Tax Rate, Rate, Taxable Value, Cess Amount
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
    "GSTIN/UIN of Recipient", "Receiver Name", "Note Number", "Note Date",
    "Note Type", "Place Of Supply", "Reverse Charge", "Note Supply Type",
    "Note Value", "Applicable % of Tax Rate", "Rate", "Taxable Value",
    "Cess Amount"
]


def map_amazon_credit_notes(df, state_code):
    """
    Map Amazon B2B CN (cdnr) to template format.
    Amazon CN columns are a near-exact match — just drop extra columns.

    Extra Amazon columns to drop:
      Invoice/Advance Receipt Number, Invoice/Advance Receipt Date,
      Reason for Issuing Document, source_gstin
    """
    state_df = df[df["source_gstin"].str[:2] == state_code].copy()
    if len(state_df) == 0:
        return pd.DataFrame(columns=TEMPLATE_COLS)

    # Drop extra columns
    for col in ["source_gstin", "Invoice/Advance Receipt Number",
                "Invoice/Advance Receipt Date", "Reason for Issuing Document"]:
        if col in state_df.columns:
            state_df = state_df.drop(columns=[col])

    # Normalize rate (Amazon may have decimal rates like 0.18)
    state_df = normalize_rate(state_df, "Rate")

    # Fill defaults
    state_df["Reverse Charge"] = state_df["Reverse Charge"].fillna("N")
    state_df["Note Type"] = state_df["Note Type"].fillna("C")
    state_df["Note Supply Type"] = state_df["Note Supply Type"].fillna("Regular B2B")
    state_df["Cess Amount"] = state_df["Cess Amount"].fillna(0)

    return state_df[TEMPLATE_COLS]


def map_einvoice_credit_notes(df):
    """
    Map E-Invoice CDNR to template format.
    E-Invoice has slight column name differences and extra columns.

    E-Invoice CDNR columns:
      GSTIN/UIN of Recipient, Receiver Name, Note Number, Note Date,
      Note Type, Place of Supply, Reverse Charge, Note Supply Type,
      Note value, Applicable % of Tax Rate, Rate, Taxable Value,
      Integrated Tax, Central Tax, State/UT Tax, Cess Amount,
      IRN, IRN date, E-invoice status, ...
    """
    df = df.copy()

    # Fix case differences
    df = df.rename(columns={
        "Place of Supply": "Place Of Supply",
        "Note value": "Note Value",
    })

    # Normalize rate
    df = normalize_rate(df, "Rate")

    # Fill defaults
    df["Reverse Charge"] = df["Reverse Charge"].fillna("N")
    df["Note Type"] = df["Note Type"].fillna("C")
    df["Note Supply Type"] = df["Note Supply Type"].fillna("Regular B2B")
    df["Cess Amount"] = df["Cess Amount"].fillna(0)

    # Drop extra E-Invoice columns (IRN, tax breakdowns, status)
    return df[TEMPLATE_COLS]


def generate_creditnotes_files(amazon_data, einvoice_data, states_dict, folders):
    """
    Generate cdnr1.csv for each state.
    Combines Amazon credit notes + E-Invoice credit notes.
    """
    amz_cn = amazon_data.get("credit_notes")

    for code, info in sorted(states_dict.items()):
        folder = folders[code]
        parts = []

        # Amazon credit notes for this seller state
        if amz_cn is not None and len(amz_cn) > 0:
            mapped = map_amazon_credit_notes(amz_cn, code)
            if len(mapped) > 0:
                parts.append(mapped)

        # E-Invoice credit notes for this state
        einv_state = einvoice_data.get(code, {})
        einv_cn = einv_state.get("credit_notes")
        if einv_cn is not None and len(einv_cn) > 0:
            mapped = map_einvoice_credit_notes(einv_cn)
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
        result = result.drop_duplicates(subset=["Note Number", "Rate"], keep="first")
        result = result.reset_index(drop=True)

        out_path = folder / "cdnr1.csv"
        result.to_csv(out_path, index=False)
        print(f"  {code}-{info['name']}: cdnr1.csv = {len(result)} rows")
