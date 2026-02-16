"""
HSN Cleaner Module

1. Clean HSN codes - remove non-numeric characters (95069920aa -> 95069920)
2. Fill empty HSN values:
   a) Taxable Value == 0 -> remove row
   b) Taxable Value != 0 -> fill using config map (or frequency fallback)
"""

import pandas as pd
from pathlib import Path


def _build_fill_map(df, hsn_col, rate_col, rate_hsn_map=None):
    """
    Build the HSN fill map. Uses rate_hsn_map from config if provided,
    falls back to frequency-based logic for any rates not in the map.
    """
    empty_mask = df[hsn_col].isna() | (df[hsn_col].astype(str).str.strip() == '')
    has_hsn = df[~empty_mask]

    # Start with config map (keys are string rates like "5", "18")
    fill_map = {}
    if rate_hsn_map:
        for rate_str, hsn_val in rate_hsn_map.items():
            fill_map[int(rate_str)] = hsn_val

    # Frequency fallback for rates not in config map
    for rate, group in has_hsn.groupby(rate_col):
        if rate not in fill_map:
            most_common = group[hsn_col].value_counts().index[0]
            fill_map[rate] = most_common

    return fill_map


def generate_empty_hsn_report(df, hsn_col, taxable_col, rate_col, output_path, rate_hsn_map=None):
    """
    Generate a CSV report of rows with empty HSN codes (after cleaning, before filling).
    Includes source info and the HSN that will be auto-assigned.
    """
    empty_mask = df[hsn_col].isna() | (df[hsn_col].astype(str).str.strip() == '')
    tax_vals = pd.to_numeric(df[taxable_col], errors='coerce').fillna(0)
    # Only report rows with non-zero taxable value (zero-value rows get deleted)
    report_mask = empty_mask & (tax_vals != 0)

    if not report_mask.any():
        print("    No empty HSN rows to report.")
        return

    fill_map = _build_fill_map(df, hsn_col, rate_col, rate_hsn_map)

    # Build report dataframe
    report_rows = []
    for idx in df[report_mask].index:
        row = df.loc[idx]
        rate = row[rate_col]
        filled_hsn = fill_map.get(rate, "NO_MATCH")
        entry = {
            "source_gstin": row.get("source_gstin", ""),
            "source_file": row.get("source_file", ""),
            "Description": row.get("Description", ""),
            "UQC": row.get("UQC", ""),
            "Total Quantity": row.get("Total Quantity", ""),
            "Rate": rate,
            "Total Value": row.get("Total Value", ""),
            "Taxable Value": row.get(taxable_col, ""),
            "Integrated Tax Amount": row.get("Integrated Tax Amount", ""),
            "Central Tax Amount": row.get("Central Tax Amount", ""),
            "State/UT Tax Amount": row.get("State/UT Tax Amount", ""),
            "filled_with_hsn": filled_hsn,
        }
        report_rows.append(entry)

    report_df = pd.DataFrame(report_rows)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)
    print(f"    Empty HSN report: {len(report_df)} rows saved to {output_path}")


def clean_hsn_codes(df, hsn_col):
    """Strip non-numeric characters from HSN codes. Returns column as string type."""
    df = df.copy()
    # Convert column to string first (handles float64 columns with NaN)
    df[hsn_col] = df[hsn_col].astype("object")
    mask = df[hsn_col].notna()
    df.loc[mask, hsn_col] = (
        df.loc[mask, hsn_col]
        .astype(str)
        .str.replace(r'[^0-9]', '', regex=True)
    )
    # Empty strings become NaN
    df[hsn_col] = df[hsn_col].replace('', pd.NA)
    return df


def fill_empty_hsn(df, hsn_col, taxable_col, rate_col, rate_hsn_map=None):
    """
    Fill empty HSN values:
    - Delete rows where HSN is empty AND taxable value is 0
    - Fill remaining empty HSN using config map (or frequency fallback)
    """
    df = df.copy()
    empty_mask = df[hsn_col].isna() | (df[hsn_col].astype(str).str.strip() == '')

    if not empty_mask.any():
        return df

    # Delete rows with empty HSN and zero taxable value
    tax_vals = pd.to_numeric(df[taxable_col], errors='coerce').fillna(0)
    delete_mask = empty_mask & (tax_vals == 0)
    if delete_mask.any():
        print(f"    Removed {delete_mask.sum()} rows (empty HSN + zero taxable)")
        df = df[~delete_mask].reset_index(drop=True)
        # Recalculate empty mask after deletion
        empty_mask = df[hsn_col].isna() | (df[hsn_col].astype(str).str.strip() == '')

    if not empty_mask.any():
        return df

    fill_map = _build_fill_map(df, hsn_col, rate_col, rate_hsn_map)

    # Fill empty HSN values
    filled = 0
    for idx in df[empty_mask].index:
        rate = df.loc[idx, rate_col]
        if rate in fill_map:
            df.loc[idx, hsn_col] = fill_map[rate]
            filled += 1

    if filled > 0:
        source = "config map" if rate_hsn_map else "rate-frequency lookup"
        print(f"    Filled {filled} empty HSN values using {source}")

    return df
