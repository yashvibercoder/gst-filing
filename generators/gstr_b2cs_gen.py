"""
GSTR B2CS Template Generator

Source: Flipkart 7A (intra) + 7B (inter) + Amazon B2C Small/Large + Meesho raw
Output: b2cs.csv per seller state, aggregated by (Place Of Supply, Rate)

Template columns:
  Type, Place Of Supply, Rate, Applicable % of Tax Rate, Taxable Value, Cess Amount
"""

import pandas as pd
from processors.state_detector import filter_by_gstin, STATE_CODE_MAP, MEESHO_STATE_MAP
from processors.rate_normalizer import normalize_rate

TEMPLATE_COLS = [
    "Type", "Place Of Supply", "Rate",
    "Applicable % of Tax Rate", "Taxable Value", "Cess Amount"
]

# Flipkart Delivered State name → GST format "XX-State Name"
_FK_STATE_LOOKUP = {name.upper(): gst for name, gst in MEESHO_STATE_MAP.items()}
# Flipkart uses different names than Meesho for some states
_FK_STATE_LOOKUP["ODISHA"] = "21-Odisha"
_FK_STATE_LOOKUP["JAMMU AND KASHMIR"] = "01-Jammu and Kashmir"
_FK_STATE_LOOKUP["PUDUCHERRY"] = "34-Puducherry"
_FK_STATE_LOOKUP["DADRA AND NAGAR HAVELI AND DAMAN AND DIU"] = "26-Dadra and Nagar Haveli"
_FK_STATE_LOOKUP["ANDAMAN AND NICOBAR"] = "35-Andaman and Nicobar Islands"


def _gst_place(state_code):
    """Build Place Of Supply string from state code: '07' → '07-Delhi'."""
    name = STATE_CODE_MAP.get(state_code, "Unknown")
    return f"{state_code}-{name}"


def map_flipkart_b2c_intra(df, seller_gstin):
    """
    Map Flipkart B2C intrastate (Section 7A) to B2CS rows.
    Intrastate: Place Of Supply = seller's own state.
    Rate = CGST% * 2 (combined rate).
    """
    df = filter_by_gstin(df, "GSTIN", seller_gstin)
    if len(df) == 0:
        return pd.DataFrame(columns=["Place Of Supply", "Rate", "Taxable Value", "Cess Amount"])

    seller_state = seller_gstin[:2]
    result = pd.DataFrame({
        "Place Of Supply": _gst_place(seller_state),
        "Rate": pd.to_numeric(df["CGST %"], errors="coerce").fillna(0) * 2,
        "Taxable Value": pd.to_numeric(df["Aggregate Taxable Value Rs."], errors="coerce").fillna(0),
        "Cess Amount": pd.to_numeric(df["CESS Amount Rs."], errors="coerce").fillna(0),
    })
    return result


def map_flipkart_b2c_inter(df, seller_gstin):
    """
    Map Flipkart B2C interstate (Section 7B) to B2CS rows.
    Interstate: Place Of Supply from Delivered State, Rate = IGST%.
    """
    df = filter_by_gstin(df, "GSTIN", seller_gstin)
    if len(df) == 0:
        return pd.DataFrame(columns=["Place Of Supply", "Rate", "Taxable Value", "Cess Amount"])

    # Convert Delivered State name to GST format "XX-State Name"
    pos = df["Delivered State (PoS)"].str.strip().str.upper().map(_FK_STATE_LOOKUP)
    unmapped = pos.isna()
    if unmapped.any():
        # Fallback: try building from Delivered State Code if name lookup fails
        for idx in pos[unmapped].index:
            state_name = str(df.loc[idx, "Delivered State (PoS)"]).strip()
            print(f"    WARNING: Unmapped Flipkart B2C inter state: {state_name}")

    result = pd.DataFrame({
        "Place Of Supply": pos,
        "Rate": pd.to_numeric(df["IGST %"], errors="coerce").fillna(0),
        "Taxable Value": pd.to_numeric(df["Aggregate Taxable Value Rs."], errors="coerce").fillna(0),
        "Cess Amount": pd.to_numeric(df["CESS Amount Rs."], errors="coerce").fillna(0),
    })
    # Drop rows with unmapped states
    result = result.dropna(subset=["Place Of Supply"])
    return result


def map_amazon_b2c_small(df, state_code):
    """
    Map Amazon B2C Small to B2CS rows.
    Amazon B2C Small columns: Type, Place Of Supply, Rate, Taxable Value, Cess Amount, ...
    Rate is decimal (0.05) — will be normalized later.
    """
    state_df = df[df["source_gstin"].str[:2] == state_code].copy()
    if len(state_df) == 0:
        return pd.DataFrame(columns=["Place Of Supply", "Rate", "Taxable Value", "Cess Amount"])

    result = pd.DataFrame({
        "Place Of Supply": state_df["Place Of Supply"],
        "Rate": pd.to_numeric(state_df["Rate"], errors="coerce").fillna(0),
        "Taxable Value": pd.to_numeric(state_df["Taxable Value"], errors="coerce").fillna(0),
        "Cess Amount": pd.to_numeric(state_df["Cess Amount"], errors="coerce").fillna(0),
    })
    return result


def map_amazon_b2c_large(df, state_code):
    """
    Map Amazon B2C Large to B2CS rows.
    B2C Large is per-invoice — will be aggregated later with other sources.
    """
    state_df = df[df["source_gstin"].str[:2] == state_code].copy()
    if len(state_df) == 0:
        return pd.DataFrame(columns=["Place Of Supply", "Rate", "Taxable Value", "Cess Amount"])

    result = pd.DataFrame({
        "Place Of Supply": state_df["Place Of Supply"],
        "Rate": pd.to_numeric(state_df["Rate"], errors="coerce").fillna(0),
        "Taxable Value": pd.to_numeric(state_df["Taxable Value"], errors="coerce").fillna(0),
        "Cess Amount": pd.to_numeric(state_df["Cess Amount"], errors="coerce").fillna(0),
    })
    return result


def map_meesho_b2c(meesho_raw, seller_gstin, config):
    """
    Map Meesho raw transactions to B2CS rows.
    Aggregate by (customer state, rate).
    """
    cols = config["meesho_columns"]
    df = meesho_raw.copy()

    agg = df.groupby([cols["state"], cols["gst_rate"]]).agg(
        taxable_value=(cols["taxable_value"], "sum"),
    ).reset_index()

    result = pd.DataFrame({
        "Place Of Supply": agg[cols["state"]],
        "Rate": pd.to_numeric(agg[cols["gst_rate"]], errors="coerce").fillna(0),
        "Taxable Value": agg["taxable_value"],
        "Cess Amount": 0.0,
    })
    return result


def generate_b2cs_files(flipkart_data, amazon_data, meesho_data,
                        states_dict, folders, config):
    """
    Generate b2cs.csv for each seller state.
    Combines Flipkart B2C + Amazon B2C + Meesho B2C, aggregated by (PoS, Rate).
    """
    fk_intra = flipkart_data.get("b2c_intra")
    fk_inter = flipkart_data.get("b2c_inter")
    amz_b2c_small = amazon_data.get("b2c_small")
    amz_b2c_large = amazon_data.get("b2c_large")
    meesho_raw = meesho_data.get("raw") if meesho_data else None
    meesho_gstin = "07IFWPS9148C1ZK"

    for code, info in sorted(states_dict.items()):
        gstin = info["gstin"]
        folder = folders[code]
        parts = []

        # Flipkart B2C Intra
        if fk_intra is not None and len(fk_intra) > 0:
            mapped = map_flipkart_b2c_intra(fk_intra, gstin)
            if len(mapped) > 0:
                parts.append(mapped)

        # Flipkart B2C Inter
        if fk_inter is not None and len(fk_inter) > 0:
            mapped = map_flipkart_b2c_inter(fk_inter, gstin)
            if len(mapped) > 0:
                parts.append(mapped)

        # Amazon B2C Small
        if amz_b2c_small is not None and len(amz_b2c_small) > 0:
            mapped = map_amazon_b2c_small(amz_b2c_small, code)
            if len(mapped) > 0:
                parts.append(mapped)

        # Amazon B2C Large
        if amz_b2c_large is not None and len(amz_b2c_large) > 0:
            mapped = map_amazon_b2c_large(amz_b2c_large, code)
            if len(mapped) > 0:
                parts.append(mapped)

        # Meesho (Delhi/07 only)
        if code == meesho_gstin[:2] and meesho_raw is not None and len(meesho_raw) > 0:
            mapped = map_meesho_b2c(meesho_raw, meesho_gstin, config)
            if len(mapped) > 0:
                parts.append(mapped)

        if not parts:
            continue

        # Combine all sources
        combined = pd.concat(parts, ignore_index=True)

        # Normalize Place Of Supply: extract state code, rebuild from STATE_CODE_MAP
        # This unifies "01-Jammu & Kashmir" (Amazon) vs "01-Jammu and Kashmir" (Flipkart)
        combined["Place Of Supply"] = combined["Place Of Supply"].apply(
            lambda pos: _gst_place(str(pos)[:2]) if str(pos)[:2] in STATE_CODE_MAP else pos
        )

        # Normalize rates to integers (0.05 → 5, 2.5 → 3, etc.)
        combined = normalize_rate(combined, "Rate")

        # Aggregate by (Place Of Supply, Rate) — sum Taxable Value and Cess
        agg = combined.groupby(["Place Of Supply", "Rate"]).agg(
            taxable=("Taxable Value", "sum"),
            cess=("Cess Amount", "sum"),
        ).reset_index()

        result = pd.DataFrame({
            "Type": "OE",
            "Place Of Supply": agg["Place Of Supply"],
            "Rate": agg["Rate"],
            "Applicable % of Tax Rate": 0,
            "Taxable Value": agg["taxable"].round(2),
            "Cess Amount": agg["cess"].round(2),
        })
        result = result[TEMPLATE_COLS]

        if len(result) == 0:
            continue

        out_path = folder / "b2cs.csv"
        result.to_csv(out_path, index=False)
        print(f"  {code}-{info['name']}: b2cs.csv = {len(result)} rows")
