"""
Documents Template Generator

Source: Flipkart Section 13 (invoice series) + B2B invoice series
Output: docs.csv per state

Template columns:
  Nature of Document, Sr. No. From, Sr. No. To, Total Number, Cancelled
"""

import re
import pandas as pd
from processors.state_detector import filter_by_gstin

TEMPLATE_COLS = [
    "Nature of Document", "Sr. No. From", "Sr. No. To",
    "Total Number", "Cancelled"
]


def _get_prefix(invoice_num):
    """Extract alphabetic prefix from invoice number (e.g., 'IN-' from 'IN-1234')."""
    m = re.match(r'^([A-Za-z\-]+)', str(invoice_num))
    return m.group(1) if m else ""


def _derive_invoice_series(b2b_df):
    """
    Derive document series rows from B2B invoice data.
    Groups by invoice prefix, finds min/max/count per series.
    """
    if b2b_df is None or len(b2b_df) == 0:
        return pd.DataFrame(columns=TEMPLATE_COLS)

    df = b2b_df.copy()
    df["_prefix"] = df["Invoice Number"].apply(_get_prefix)

    rows = []
    for prefix, group in df.groupby("_prefix"):
        if not prefix:
            continue
        invoices = group["Invoice Number"].sort_values()
        rows.append({
            "Nature of Document": "Invoices for outward supply",
            "Sr. No. From": invoices.iloc[0],
            "Sr. No. To": invoices.iloc[-1],
            "Total Number": len(invoices),
            "Cancelled": 0,
        })

    if not rows:
        return pd.DataFrame(columns=TEMPLATE_COLS)
    return pd.DataFrame(rows)[TEMPLATE_COLS]


def map_flipkart_documents(df):
    """Map Flipkart Section 13 columns to template format."""
    df = df.copy()
    df = df.rename(columns={
        "Invoice Series From": "Sr. No. From",
        "Invoice Series \nTo": "Sr. No. To",
        "Total Number of Invoices": "Total Number",
        "Cancelled if any": "Cancelled",
    })
    df["Nature of Document"] = "Invoices for outward supply"
    if "GSTIN" in df.columns:
        df = df.drop(columns=["GSTIN"])
    if "Net invoices Issued" in df.columns:
        df = df.drop(columns=["Net invoices Issued"])
    return df[TEMPLATE_COLS]


def generate_documents_files(flipkart_data, b2b_data, states_dict, folders):
    """
    Generate docs.csv for each state.
    Combines Flipkart Section 13 + derived invoice series from B2B output.
    b2b_data: dict with 'b2b_by_state' key mapping state_code -> b2b DataFrame
    """
    fk_docs = flipkart_data.get("documents")

    for code, info in sorted(states_dict.items()):
        gstin = info["gstin"]
        parts = []

        # Flipkart documents for this seller state
        if fk_docs is not None and len(fk_docs) > 0:
            state_docs = filter_by_gstin(fk_docs, "GSTIN", gstin)
            if len(state_docs) > 0:
                fk_mapped = map_flipkart_documents(state_docs)
                if len(fk_mapped) > 0:
                    parts.append(fk_mapped)

        # Derive invoice series from B2B data
        state_b2b = b2b_data.get(code)
        if state_b2b is not None and len(state_b2b) > 0:
            b2b_series = _derive_invoice_series(state_b2b)
            if len(b2b_series) > 0:
                # Skip series that Flipkart already covers (by prefix)
                fk_prefixes = set()
                if parts:
                    for _, row in parts[0].iterrows():
                        fk_prefixes.add(_get_prefix(row["Sr. No. From"]))
                b2b_series["_prefix"] = b2b_series["Sr. No. From"].apply(_get_prefix)
                b2b_series = b2b_series[~b2b_series["_prefix"].isin(fk_prefixes)]
                b2b_series = b2b_series.drop(columns=["_prefix"])
                if len(b2b_series) > 0:
                    parts.append(b2b_series)

        if not parts:
            continue

        result = pd.concat(parts, ignore_index=True)
        out_path = folders[code] / "docs.csv"
        result.to_csv(out_path, index=False)
        print(f"  {code}-{info['name']}: docs.csv = {len(result)} rows")
