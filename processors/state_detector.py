"""
State Detector Module
- Normalizes Meesho state names to GST portal format ("XX-State Name")
- Detects seller states across all platforms
- Creates per-state output folders
"""

from pathlib import Path

# Meesho plain name -> GST portal "code-name" format
MEESHO_STATE_MAP = {
    "ANDHRA PRADESH": "37-Andhra Pradesh",
    "ARUNACHAL PRADESH": "12-Arunachal Pradesh",
    "ASSAM": "18-Assam",
    "BIHAR": "10-Bihar",
    "CHANDIGARH": "04-Chandigarh",
    "CHHATTISGARH": "22-Chhattisgarh",
    "DAMAN": "25-Daman and Diu",
    "DELHI": "07-Delhi",
    "GOA": "30-Goa",
    "GUJARAT": "24-Gujarat",
    "HARYANA": "06-Haryana",
    "HIMACHAL PRADESH": "02-Himachal Pradesh",
    "JAMMU & KASHMIR": "01-Jammu and Kashmir",
    "JHARKHAND": "20-Jharkhand",
    "KARNATAKA": "29-Karnataka",
    "KERALA": "32-Kerala",
    "MADHYA PRADESH": "23-Madhya Pradesh",
    "MAHARASHTRA": "27-Maharashtra",
    "MANIPUR": "14-Manipur",
    "MEGHALAYA": "17-Meghalaya",
    "MIZORAM": "15-Mizoram",
    "NAGALAND": "13-Nagaland",
    "ORISSA": "21-Odisha",
    "PONDICHERRY": "34-Puducherry",
    "PUNJAB": "03-Punjab",
    "RAJASTHAN": "08-Rajasthan",
    "SIKKIM": "11-Sikkim",
    "TAMIL NADU": "33-Tamil Nadu",
    "TELANGANA": "36-Telangana",
    "TRIPURA": "16-Tripura",
    "UTTAR PRADESH": "09-Uttar Pradesh",
    "UTTARAKHAND": "05-Uttarakhand",
    "WEST BENGAL": "19-West Bengal",
    "DADRA AND NAGAR HAVELI": "26-Dadra and Nagar Haveli",
    "LAKSHADWEEP": "31-Lakshadweep",
    "ANDAMAN AND NICOBAR ISLANDS": "35-Andaman and Nicobar Islands",
    "LADAKH": "38-Ladakh",
}

# State code -> State name (derived from MEESHO_STATE_MAP)
STATE_CODE_MAP = {}
for _val in MEESHO_STATE_MAP.values():
    _code, _name = _val.split("-", 1)
    STATE_CODE_MAP[_code] = _name


def normalize_meesho_states(df, state_col="end_customer_state_new"):
    """Convert Meesho plain state names to GST portal format."""
    df = df.copy()
    df[state_col] = df[state_col].str.strip().str.upper().map(MEESHO_STATE_MAP)
    unmapped = df[df[state_col].isna()]
    if len(unmapped) > 0:
        print(f"    WARNING: {len(unmapped)} rows with unmapped states")
    return df


def _gstin_to_state_code(gstin):
    """Extract 2-digit state code from a GSTIN."""
    return str(gstin)[:2]


def detect_seller_states(flipkart_data, amazon_data, meesho_data, amazon_file_paths, einvoice_file_paths=None):
    """
    Detect all seller states across platforms.
    Returns: {state_code: {"gstin": str, "name": str, "platforms": [str]}}
    """
    states = {}

    # Amazon: extract GSTIN from each filename
    for fpath in amazon_file_paths:
        fname = fpath.name if hasattr(fpath, 'name') else str(Path(fpath).name)
        if "A3SZBDZ05A1P39-" in fname:
            gstin = fname.split("A3SZBDZ05A1P39-")[-1].split(".")[0]
            code = _gstin_to_state_code(gstin)
            if code not in states:
                states[code] = {"gstin": gstin, "name": STATE_CODE_MAP.get(code, "Unknown"), "platforms": []}
            if "amazon" not in states[code]["platforms"]:
                states[code]["platforms"].append("amazon")

    # E-Invoice: extract GSTIN from each filename (EINV_<GSTIN>_<YEAR>.xlsx)
    if einvoice_file_paths:
        for fpath in einvoice_file_paths:
            fname = fpath.name if hasattr(fpath, 'name') else str(Path(fpath).name)
            parts = fname.replace('.xlsx', '').split('_')
            if len(parts) >= 2:
                gstin = parts[1]
                code = _gstin_to_state_code(gstin)
                if code not in states:
                    states[code] = {"gstin": gstin, "name": STATE_CODE_MAP.get(code, "Unknown"), "platforms": []}
                if "einvoice" not in states[code]["platforms"]:
                    states[code]["platforms"].append("einvoice")

    # Flipkart: extract unique GSTINs from data
    for key, df in flipkart_data.items():
        if df is not None and "GSTIN" in df.columns:
            for gstin in df["GSTIN"].dropna().unique():
                code = _gstin_to_state_code(gstin)
                if code not in states:
                    states[code] = {"gstin": gstin, "name": STATE_CODE_MAP.get(code, "Unknown"), "platforms": []}
                if "flipkart" not in states[code]["platforms"]:
                    states[code]["platforms"].append("flipkart")

    # Meesho: extract unique GSTINs
    if meesho_data and meesho_data.get("raw") is not None:
        raw = meesho_data["raw"]
        if "gstin" in raw.columns:
            for gstin in raw["gstin"].dropna().unique():
                code = _gstin_to_state_code(gstin)
                if code not in states:
                    states[code] = {"gstin": gstin, "name": STATE_CODE_MAP.get(code, "Unknown"), "platforms": []}
                if "meesho" not in states[code]["platforms"]:
                    states[code]["platforms"].append("meesho")

    return states


def create_state_folders(states_dict, output_root):
    """
    Create output/{state_code}-{State Name}/ for each state with data.
    Returns: {state_code: Path}
    """
    output_root = Path(output_root)
    folders = {}
    for code, info in sorted(states_dict.items()):
        folder_name = f"{code}-{info['name']}"
        folder_path = output_root / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        folders[code] = folder_path
    return folders


def filter_by_gstin(df, gstin_col, gstin):
    """Filter DataFrame to rows matching a specific seller GSTIN."""
    return df[df[gstin_col] == gstin].copy()
