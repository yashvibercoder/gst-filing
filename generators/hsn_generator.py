"""
HSN Generator Module
Generates HSN B2B and HSN B2C output CSV files per state.

Logic:
- Total HSN = Amazon + Flipkart + Meesho HSN (per state, by seller GSTIN)
- HSN B2B = E-Invoice hsn(b2b) directly (for states with E-Invoice data)
- HSN B2C = Total HSN minus E-Invoice HSN B2B
- States without E-Invoice: all HSN goes to B2C
"""

import pandas as pd
from pathlib import Path
from processors.rate_normalizer import normalize_rate
from processors.state_detector import filter_by_gstin

# Map short UQC codes to GST portal long format
UQC_LONG_MAP = {
    "BAG": "BAG-BAGS",
    "BAL": "BAL-BALE",
    "BDL": "BDL-BUNDLES",
    "BKL": "BKL-BUCKLES",
    "BOU": "BOU-BILLION OF UNITS",
    "BOX": "BOX-BOX",
    "BTL": "BTL-BOTTLES",
    "BUN": "BUN-BUNCHES",
    "CAN": "CAN-CANS",
    "CBM": "CBM-CUBIC METERS",
    "CCM": "CCM-CUBIC CENTIMETERS",
    "CMS": "CMS-CENTIMETERS",
    "CTN": "CTN-CARTONS",
    "DOZ": "DOZ-DOZENS",
    "DRM": "DRM-DRUMS",
    "GGK": "GGK-GREAT GROSS",
    "GMS": "GMS-GRAMMES",
    "GRS": "GRS-GROSS",
    "GYD": "GYD-GROSS YARDS",
    "KGS": "KGS-KILOGRAMS",
    "KLR": "KLR-KILOLITRE",
    "KME": "KME-KILOMETRE",
    "LTR": "LTR-LITRES",
    "MLT": "MLT-MILILITRE",
    "MTR": "MTR-METERS",
    "MTS": "MTS-METRIC TON",
    "NOS": "NOS-NUMBERS",
    "OTH": "OTH-OTHERS",
    "PAC": "PAC-PACKS",
    "PCS": "PCS-PIECES",
    "PRS": "PRS-PAIRS",
    "QTL": "QTL-QUINTAL",
    "ROL": "ROL-ROLLS",
    "SET": "SET-SETS",
    "SQF": "SQF-SQUARE FEET",
    "SQM": "SQM-SQUARE METERS",
    "SQY": "SQY-SQUARE YARDS",
    "TBS": "TBS-TABLETS",
    "TGM": "TGM-TEN GROSS",
    "THD": "THD-THOUSANDS",
    "TON": "TON-TONNES",
    "TUB": "TUB-TUBES",
    "UGS": "UGS-US GALLONS",
    "UNT": "UNT-UNITS",
    "YDS": "YDS-YARDS",
}

def _normalize_hsn(code):
    """Truncate HSN to 8 digits. Amazon appends a trailing 0, producing 9-digit codes."""
    s = str(code).strip()
    return s[:8] if len(s) > 8 else s


# Template column order
TEMPLATE_COLS = [
    "HSN", "Description", "UQC", "Total Quantity", "Total Value",
    "Taxable Value", "Integrated Tax Amount", "Central Tax Amount",
    "State/UT Tax Amount", "Cess Amount", "Rate"
]


def map_einvoice_hsn_b2b(df):
    """Map E-Invoice hsn(b2b) columns to template format."""
    df = df.copy()
    df = df.rename(columns={
        "Total taxable value": "Taxable Value",
        "Integrated tax": "Integrated Tax Amount",
        "Central tax": "Central Tax Amount",
        "State/UT tax": "State/UT Tax Amount",
        "Cess": "Cess Amount",
        "Rate (%)": "Rate",
    })
    # Calculate Total Value = Taxable + all taxes
    df["Total Value"] = (
        df["Taxable Value"].fillna(0)
        + df["Integrated Tax Amount"].fillna(0)
        + df["Central Tax Amount"].fillna(0)
        + df["State/UT Tax Amount"].fillna(0)
        + df["Cess Amount"].fillna(0)
    )
    df = normalize_rate(df, "Rate")
    df["HSN"] = df["HSN"].astype(str).apply(_normalize_hsn)
    return df[TEMPLATE_COLS]


def map_amazon_hsn(df):
    """Map Amazon HSN columns to template format (near-perfect match)."""
    df = df.copy()
    # Drop source tracking columns
    for col in ["source_file", "source_gstin"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    df = normalize_rate(df, "Rate")
    df["HSN"] = df["HSN"].astype(str).apply(_normalize_hsn)
    return df[TEMPLATE_COLS]


def map_flipkart_hsn(df):
    """Map Flipkart HSN columns to template format."""
    df = df.copy()
    df = df.rename(columns={
        "HSN Number": "HSN",
        "Total Quantity in Nos.": "Total Quantity",
        "Total\n Value Rs.": "Total Value",
        "Total Taxable Value Rs.": "Taxable Value",
        "IGST Amount Rs.": "Integrated Tax Amount",
        "CGST Amount Rs.": "Central Tax Amount",
        "SGST Amount Rs.": "State/UT Tax Amount",
        "Cess Rs.": "Cess Amount",
    })
    # Fill missing columns
    if "Description" not in df.columns:
        df["Description"] = ""
    if "UQC" not in df.columns:
        df["UQC"] = ""
    # Derive Rate from total tax / taxable value
    taxable = pd.to_numeric(df["Taxable Value"], errors="coerce").fillna(0)
    total_tax = (
        pd.to_numeric(df["Integrated Tax Amount"], errors="coerce").fillna(0)
        + pd.to_numeric(df["Central Tax Amount"], errors="coerce").fillna(0)
        + pd.to_numeric(df["State/UT Tax Amount"], errors="coerce").fillna(0)
    )
    rate_pct = (total_tax / taxable.replace(0, pd.NA)).fillna(0) * 100
    # Snap to nearest standard GST rate (0, 5, 12, 18, 28)
    standard_rates = [0, 5, 12, 18, 28]
    df["Rate"] = rate_pct.apply(
        lambda x: min(standard_rates, key=lambda r: abs(r - x))
    )
    # Drop GSTIN (not in template)
    if "GSTIN" in df.columns:
        df = df.drop(columns=["GSTIN"])
    return df[TEMPLATE_COLS]


def map_meesho_hsn(df, seller_gstin, config):
    """Aggregate Meesho raw transactions into HSN template format."""
    df = df.copy()
    cols = config["meesho_columns"]
    seller_state = seller_gstin[:2]

    # Determine intrastate vs interstate for tax split
    # Meesho states are already normalized to "XX-State Name" by Phase 3
    df["_is_intra"] = df[cols["state"]].str[:2] == seller_state

    # Split tax_amount into IGST / CGST+SGST
    tax = pd.to_numeric(df[cols["tax_amount"]], errors="coerce").fillna(0)
    df["_igst"] = 0.0
    df["_cgst"] = 0.0
    df["_sgst"] = 0.0
    df.loc[~df["_is_intra"], "_igst"] = tax[~df["_is_intra"]]
    df.loc[df["_is_intra"], "_cgst"] = tax[df["_is_intra"]] / 2
    df.loc[df["_is_intra"], "_sgst"] = tax[df["_is_intra"]] / 2

    # Aggregate by HSN + Rate
    agg = df.groupby([cols["hsn_code"], cols["gst_rate"]]).agg(
        total_qty=(cols["quantity"], "sum"),
        total_value=(cols["invoice_value"], "sum"),
        taxable_value=(cols["taxable_value"], "sum"),
        igst=("_igst", "sum"),
        cgst=("_cgst", "sum"),
        sgst=("_sgst", "sum"),
    ).reset_index()

    result = pd.DataFrame({
        "HSN": agg[cols["hsn_code"]].astype(str),
        "Description": "",
        "UQC": "",
        "Total Quantity": agg["total_qty"],
        "Total Value": agg["total_value"],
        "Taxable Value": agg["taxable_value"],
        "Integrated Tax Amount": agg["igst"],
        "Central Tax Amount": agg["cgst"],
        "State/UT Tax Amount": agg["sgst"],
        "Cess Amount": 0.0,
        "Rate": agg[cols["gst_rate"]],
    })
    return result[TEMPLATE_COLS]


def subtract_b2b_from_total(total_hsn, einvoice_hsn_b2b):
    """
    Subtract E-Invoice B2B values from total HSN to get B2C.
    Match on HSN (as string) + Rate. Subtract numeric columns.
    """
    total = total_hsn.copy()
    b2b = einvoice_hsn_b2b.copy()

    # Ensure HSN is string for matching, normalize to 8-digit standard
    total["HSN"] = total["HSN"].astype(str).str.strip().apply(_normalize_hsn)
    b2b["HSN"] = b2b["HSN"].astype(str).str.strip().apply(_normalize_hsn)

    numeric_cols = [
        "Total Quantity", "Total Value", "Taxable Value",
        "Integrated Tax Amount", "Central Tax Amount",
        "State/UT Tax Amount", "Cess Amount"
    ]

    # Aggregate B2B by HSN+Rate (in case of duplicate keys)
    b2b_agg = b2b.groupby(["HSN", "Rate"])[numeric_cols].sum().reset_index()

    # Merge and subtract
    merged = total.merge(
        b2b_agg, on=["HSN", "Rate"], how="left", suffixes=("", "_b2b")
    )
    for col in numeric_cols:
        b2b_col = f"{col}_b2b"
        if b2b_col in merged.columns:
            merged[col] = merged[col] - merged[b2b_col].fillna(0)
            merged = merged.drop(columns=[b2b_col])

    # Round numeric columns to 2 decimal places after subtraction
    for col in numeric_cols:
        merged[col] = merged[col].round(2)

    # Remove rows where taxable value is zero or negative
    merged = merged[merged["Taxable Value"] > 0.005].reset_index(drop=True)

    return merged[TEMPLATE_COLS]


def _most_common_hsn(hsn_df, rate):
    """Return the HSN code with the highest Taxable Value for the given rate."""
    subset = hsn_df[hsn_df["Rate"] == rate]
    if len(subset) == 0:
        return "9999"
    return subset.loc[subset["Taxable Value"].idxmax(), "HSN"]


def _compute_tax_split(df, rate, state_code, taxable_diff, cess_diff):
    """
    Derive IGST / CGST / SGST for a correction row.
    Uses the same IGST:CGST ratio as existing B2B rows at this rate.
    df must have 'Place Of Supply' and 'Taxable Value' columns.
    """
    subset = df[df["Rate"] == rate].copy()
    if len(subset) == 0 or taxable_diff == 0:
        return 0.0, 0.0, 0.0

    tv = pd.to_numeric(subset["Taxable Value"], errors="coerce").fillna(0)
    is_inter = subset["Place Of Supply"].astype(str).str[:2] != state_code
    igst_total = tv[is_inter].sum()
    intra_total = tv[~is_inter].sum()
    grand = igst_total + intra_total

    if grand == 0:
        igst_frac = 0.0
    else:
        igst_frac = igst_total / grand

    igst_taxable = taxable_diff * igst_frac
    intra_taxable = taxable_diff * (1 - igst_frac)

    igst = round(igst_taxable * rate / 100, 2)
    cgst = round(intra_taxable * rate / 200, 2)
    sgst = round(intra_taxable * rate / 200, 2)
    return igst, cgst, sgst


def reconcile_hsn_with_b2b(hsn_b2b_df, b2b_df, state_code):
    """
    Compare HSN B2B totals vs B2B invoice totals (grouped by Rate).
    Append one correction row per Rate where Taxable Value differs by > 0.01.
    Returns (updated_df, corrections_made: int).
    """
    if b2b_df is None or len(b2b_df) == 0:
        return hsn_b2b_df, 0

    b2b_by_rate = (
        b2b_df.groupby("Rate")
        .agg(taxable=("Taxable Value", "sum"), cess=("Cess Amount", "sum"))
        .reset_index()
    )
    hsn_by_rate = (
        hsn_b2b_df.groupby("Rate")
        .agg(taxable=("Taxable Value", "sum"), cess=("Cess Amount", "sum"))
        .reset_index()
    )

    merged = b2b_by_rate.merge(hsn_by_rate, on="Rate", how="left",
                                suffixes=("_b2b", "_hsn"))
    merged["taxable_hsn"] = merged["taxable_hsn"].fillna(0)
    merged["cess_hsn"] = merged["cess_hsn"].fillna(0)

    corrections = 0
    new_rows = []
    for _, row in merged.iterrows():
        diff_taxable = round(row["taxable_b2b"] - row["taxable_hsn"], 2)
        diff_cess = round(row["cess_b2b"] - row["cess_hsn"], 2)
        rate = row["Rate"]

        if abs(diff_taxable) < 0.01 and abs(diff_cess) < 0.01:
            continue

        igst, cgst, sgst = _compute_tax_split(b2b_df, rate, state_code,
                                               diff_taxable, diff_cess)
        total_val = round(diff_taxable + igst + cgst + sgst + diff_cess, 2)
        hsn_code = _most_common_hsn(hsn_b2b_df, rate)

        new_rows.append({
            "HSN": hsn_code,
            "Description": "",
            "UQC": "OTH-OTHERS",
            "Total Quantity": 0,
            "Total Value": total_val,
            "Taxable Value": diff_taxable,
            "Integrated Tax Amount": igst,
            "Central Tax Amount": cgst,
            "State/UT Tax Amount": sgst,
            "Cess Amount": diff_cess,
            "Rate": rate,
        })
        corrections += 1
        print(f"      HSN B2B reconcile: Rate={rate}%, diff=₹{diff_taxable:,.2f} → correction row added (HSN {hsn_code})")

    if new_rows:
        hsn_b2b_df = pd.concat(
            [hsn_b2b_df, pd.DataFrame(new_rows)], ignore_index=True
        )
    return hsn_b2b_df, corrections


def reconcile_hsn_with_b2cs(hsn_b2c_df, b2cs_df, state_code):
    """
    Compare HSN B2C totals vs B2CS totals (grouped by Rate).
    Append one correction row per Rate where Taxable Value differs by > 0.01.
    B2CS has no IGST/CGST breakdown — derive from Place Of Supply vs state_code.
    Returns (updated_df, corrections_made: int).
    """
    if b2cs_df is None or len(b2cs_df) == 0:
        return hsn_b2c_df, 0

    b2cs_by_rate = (
        b2cs_df.groupby("Rate")
        .agg(taxable=("Taxable Value", "sum"), cess=("Cess Amount", "sum"))
        .reset_index()
    )
    hsn_by_rate = (
        hsn_b2c_df.groupby("Rate")
        .agg(taxable=("Taxable Value", "sum"), cess=("Cess Amount", "sum"))
        .reset_index()
    )

    merged = b2cs_by_rate.merge(hsn_by_rate, on="Rate", how="left",
                                 suffixes=("_b2cs", "_hsn"))
    merged["taxable_hsn"] = merged["taxable_hsn"].fillna(0)
    merged["cess_hsn"] = merged["cess_hsn"].fillna(0)

    corrections = 0
    new_rows = []
    for _, row in merged.iterrows():
        diff_taxable = round(row["taxable_b2cs"] - row["taxable_hsn"], 2)
        diff_cess = round(row["cess_b2cs"] - row["cess_hsn"], 2)
        rate = row["Rate"]

        if abs(diff_taxable) < 0.01 and abs(diff_cess) < 0.01:
            continue

        igst, cgst, sgst = _compute_tax_split(b2cs_df, rate, state_code,
                                               diff_taxable, diff_cess)
        total_val = round(diff_taxable + igst + cgst + sgst + diff_cess, 2)
        hsn_code = _most_common_hsn(hsn_b2c_df, rate)

        new_rows.append({
            "HSN": hsn_code,
            "Description": "",
            "UQC": "OTH-OTHERS",
            "Total Quantity": 0,
            "Total Value": total_val,
            "Taxable Value": diff_taxable,
            "Integrated Tax Amount": igst,
            "Central Tax Amount": cgst,
            "State/UT Tax Amount": sgst,
            "Cess Amount": diff_cess,
            "Rate": rate,
        })
        corrections += 1
        print(f"      HSN B2C reconcile: Rate={rate}%, diff=₹{diff_taxable:,.2f} → correction row added (HSN {hsn_code})")

    if new_rows:
        hsn_b2c_df = pd.concat(
            [hsn_b2c_df, pd.DataFrame(new_rows)], ignore_index=True
        )
    return hsn_b2c_df, corrections


def generate_hsn_files(einvoice_data, amazon_hsn, flipkart_hsn, meesho_raw,
                       states_dict, folders, config,
                       b2b_by_state=None, b2cs_by_state=None):
    """
    Generate HSN B2B and HSN B2C files for each state.
    einvoice_data: dict keyed by state code {"07": {"hsn_b2b": df, ...}, ...}
    """
    meesho_gstin = "07IFWPS9148C1ZK"  # Meesho only has Delhi GSTIN

    for code, info in sorted(states_dict.items()):
        gstin = info["gstin"]
        folder = folders[code]
        parts = []

        # Amazon HSN for this state (filter by source_gstin)
        if amazon_hsn is not None and "source_gstin" in amazon_hsn.columns:
            amz_state = amazon_hsn[amazon_hsn["source_gstin"] == gstin.split("IFWPS")[0] + "IFWPS" + gstin.split("IFWPS")[1]]
            # Simpler: filter by state code prefix in source_gstin
            amz_state = amazon_hsn[amazon_hsn["source_gstin"].str[:2] == code]
            if len(amz_state) > 0:
                parts.append(map_amazon_hsn(amz_state))

        # Flipkart HSN for this state
        if flipkart_hsn is not None and "GSTIN" in flipkart_hsn.columns:
            fk_state = filter_by_gstin(flipkart_hsn, "GSTIN", gstin)
            if len(fk_state) > 0:
                parts.append(map_flipkart_hsn(fk_state))

        # Meesho HSN (only for Delhi/07)
        if code == meesho_gstin[:2] and meesho_raw is not None:
            meesho_mapped = map_meesho_hsn(meesho_raw, meesho_gstin, config)
            if len(meesho_mapped) > 0:
                parts.append(meesho_mapped)

        if not parts:
            continue

        # Combine all sources into Total HSN
        total_hsn = pd.concat(parts, ignore_index=True)

        # Check if E-Invoice exists for this state
        einv_state = einvoice_data.get(code, {})
        einv_hsn_b2b = einv_state.get("hsn_b2b")

        if einv_hsn_b2b is not None and len(einv_hsn_b2b) > 0:
            # Map E-Invoice HSN B2B to template format
            hsn_b2b = map_einvoice_hsn_b2b(einv_hsn_b2b)

            # Convert UQC to long format
            hsn_b2b["UQC"] = hsn_b2b["UQC"].map(
                lambda x: UQC_LONG_MAP.get(str(x).strip().upper(), x) if pd.notna(x) and str(x).strip() else x
            )

            # Reconcile HSN B2B totals against B2B invoice totals
            if b2b_by_state and code in b2b_by_state:
                hsn_b2b, n_corr = reconcile_hsn_with_b2b(
                    hsn_b2b, b2b_by_state[code], code
                )

            # Write HSN B2B
            b2b_path = folder / "hsn(b2b).csv"
            hsn_b2b.to_csv(b2b_path, index=False)
            print(f"  {code}-{info['name']}: hsn(b2b).csv = {len(hsn_b2b)} rows")

            # Subtract B2B from total to get B2C
            hsn_b2c = subtract_b2b_from_total(total_hsn, hsn_b2b)
        else:
            # No E-Invoice: all HSN is B2C
            hsn_b2c = total_hsn

        if len(hsn_b2c) > 0:
            # Convert UQC to long format
            hsn_b2c["UQC"] = hsn_b2c["UQC"].map(
                lambda x: UQC_LONG_MAP.get(str(x).strip().upper(), x) if pd.notna(x) and str(x).strip() else x
            )

            # Reconcile HSN B2C totals against B2CS totals
            if b2cs_by_state and code in b2cs_by_state:
                hsn_b2c, n_corr = reconcile_hsn_with_b2cs(
                    hsn_b2c, b2cs_by_state[code], code
                )

            b2c_path = folder / "hsn(b2c).csv"
            hsn_b2c.to_csv(b2c_path, index=False)
            print(f"  {code}-{info['name']}: hsn(b2c).csv = {len(hsn_b2c)} rows")
