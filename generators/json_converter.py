"""
GSTR-1 JSON Converter

Reads the 7 CSV files per state and produces a gstr1.json matching
the GSTN API schema for GSTR-1 filing.

Usage:
    from generators.json_converter import generate_json_for_state
    generate_json_for_state(state_folder, gstin, filing_period, seller_state_code)
"""

import json
import csv
from pathlib import Path
from collections import defaultdict


def _read_csv(path):
    """Read CSV file and return list of dicts. Returns [] if file missing."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _pos_code(pos_str):
    """Extract 2-digit state code from Place Of Supply string: '07-Delhi' → '07'."""
    return str(pos_str).strip()[:2]


def _float(val, default=0.0):
    """Safely parse float."""
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return default


def _int(val, default=0):
    """Safely parse int."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _convert_date(date_str):
    """Convert date formats to DD-MM-YYYY.
    Handles: '30-Jan-2026', '03-01-2026', '2026-01-30', etc.
    """
    import re
    s = str(date_str).strip()

    # Already DD-MM-YYYY
    if re.match(r'^\d{2}-\d{2}-\d{4}$', s):
        return s

    # DD-Mon-YYYY (e.g. 30-Jan-2026)
    months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    m = re.match(r'^(\d{2})-([A-Za-z]{3})-(\d{4})$', s)
    if m:
        day, mon, year = m.groups()
        return f"{day}-{months.get(mon.lower(), '01')}-{year}"

    return s


def _inv_type_code(inv_type_str):
    """Convert Invoice Type string to GSTN code."""
    mapping = {
        "Regular B2B": "R",
        "Regular": "R",
        "SEZ supplies with payment": "SEWP",
        "SEZ with payment": "SEWP",
        "SEZ supplies without payment": "SEWOP",
        "SEZ without payment": "SEWOP",
        "Deemed Exp": "DE",
        "Deemed Export": "DE",
    }
    return mapping.get(str(inv_type_str).strip(), "R")


def _note_type_code(note_type_str):
    """Convert Note Type to GSTN code: C → C, D → D."""
    t = str(note_type_str).strip().upper()
    return "C" if t.startswith("C") else "D"


def _supply_type_code(note_supply_str):
    """Convert Note Supply Type string to GSTN code."""
    mapping = {
        "Regular B2B": "R",
        "Regular": "R",
        "SEZ supplies with payment": "SEWP",
        "SEZ with payment": "SEWP",
        "SEZ supplies without payment": "SEWOP",
        "SEZ without payment": "SEWOP",
        "Deemed Exp": "DE",
        "Deemed Export": "DE",
    }
    return mapping.get(str(note_supply_str).strip(), "R")


def _compute_taxes(txval, rate, seller_state, pos):
    """Compute IGST/CGST/SGST from taxable value, rate, and state codes."""
    iamt = 0.0
    camt = 0.0
    samt = 0.0
    if seller_state == pos:
        # Intra-state: split into CGST + SGST
        camt = round(txval * rate / 200, 2)
        samt = camt
    else:
        # Inter-state: full IGST
        iamt = round(txval * rate / 100, 2)
    return iamt, camt, samt


def _build_b2b(rows, seller_state):
    """Convert B2B CSV rows to GSTN b2b JSON structure."""
    if not rows:
        return []

    # Group by (ctin, inum)
    invoices = defaultdict(list)
    for row in rows:
        ctin = row.get("GSTIN/UIN of Recipient", "").strip()
        inum = row.get("Invoice Number", "").strip()
        invoices[(ctin, inum)].append(row)

    # Group by ctin
    by_ctin = defaultdict(list)
    for (ctin, inum), items in invoices.items():
        first = items[0]
        pos = _pos_code(first.get("Place Of Supply", ""))
        inv_val = _float(first.get("Invoice Value"))
        rchrg = str(first.get("Reverse Charge", "N")).strip() or "N"
        inv_typ = _inv_type_code(first.get("Invoice Type", ""))
        ecom = first.get("E-Commerce GSTIN", "").strip()

        itms = []
        for item in items:
            rate = _int(item.get("Rate", 0))
            txval = _float(item.get("Taxable Value"))
            csamt = _float(item.get("Cess Amount"))
            iamt, camt, samt = _compute_taxes(txval, rate, seller_state, pos)
            itms.append({
                "num": len(itms) + 1,
                "itm_det": {
                    "rt": rate,
                    "txval": txval,
                    "iamt": iamt,
                    "camt": camt,
                    "samt": samt,
                    "csamt": csamt,
                }
            })

        inv_entry = {
            "inum": inum,
            "idt": _convert_date(first.get("Invoice date", "")),
            "val": inv_val,
            "pos": pos,
            "rchrg": rchrg,
            "inv_typ": inv_typ,
            "itms": itms,
        }
        if ecom:
            inv_entry["etin"] = ecom

        by_ctin[ctin].append(inv_entry)

    result = []
    for ctin, inv_list in sorted(by_ctin.items()):
        result.append({"ctin": ctin, "inv": inv_list})
    return result


def _build_b2cs(rows, seller_state):
    """Convert B2CS CSV rows to GSTN b2cs JSON structure."""
    if not rows:
        return []

    result = []
    for row in rows:
        pos = _pos_code(row.get("Place Of Supply", ""))
        rate = _int(row.get("Rate", 0))
        txval = _float(row.get("Taxable Value"))
        csamt = _float(row.get("Cess Amount"))
        typ = row.get("Type", "OE").strip()

        sply_ty = "INTRA" if seller_state == pos else "INTER"
        iamt, camt, samt = _compute_taxes(txval, rate, seller_state, pos)

        entry = {
            "sply_ty": sply_ty,
            "rt": rate,
            "typ": typ,
            "pos": pos,
            "txval": txval,
            "csamt": csamt,
        }
        if sply_ty == "INTER":
            entry["iamt"] = iamt
        else:
            entry["camt"] = camt
            entry["samt"] = samt

        result.append(entry)
    return result


def _build_cdnr(rows, seller_state):
    """Convert Credit Notes CSV rows to GSTN cdnr JSON structure."""
    if not rows:
        return []

    # Group by (ctin, note_num)
    notes = defaultdict(list)
    for row in rows:
        ctin = row.get("GSTIN/UIN of Recipient", "").strip()
        nt_num = row.get("Note Number", "").strip()
        notes[(ctin, nt_num)].append(row)

    by_ctin = defaultdict(list)
    for (ctin, nt_num), items in notes.items():
        first = items[0]
        pos = _pos_code(first.get("Place Of Supply", ""))
        nt_dt = _convert_date(first.get("Note Date", ""))
        ntty = _note_type_code(first.get("Note Type", "C"))
        val = _float(first.get("Note Value"))
        rchrg = str(first.get("Reverse Charge", "N")).strip() or "N"
        inv_typ = _supply_type_code(first.get("Note Supply Type", ""))

        itms = []
        for item in items:
            rate = _int(item.get("Rate", 0))
            txval = _float(item.get("Taxable Value"))
            csamt = _float(item.get("Cess Amount"))
            iamt, camt, samt = _compute_taxes(txval, rate, seller_state, pos)
            itms.append({
                "num": len(itms) + 1,
                "itm_det": {
                    "rt": rate,
                    "txval": txval,
                    "iamt": iamt,
                    "camt": camt,
                    "samt": samt,
                    "csamt": csamt,
                }
            })

        by_ctin[ctin].append({
            "ntty": ntty,
            "nt_num": nt_num,
            "nt_dt": nt_dt,
            "val": val,
            "pos": pos,
            "rchrg": rchrg,
            "inv_typ": inv_typ,
            "itms": itms,
        })

    result = []
    for ctin, nt_list in sorted(by_ctin.items()):
        result.append({"ctin": ctin, "nt": nt_list})
    return result


def _build_hsn(b2b_rows, b2c_rows):
    """Combine HSN B2B + B2C into GSTN hsn structure."""
    data = []
    for row in (b2b_rows + b2c_rows):
        hsn_sc = str(row.get("HSN", "")).strip()
        if not hsn_sc:
            continue
        data.append({
            "hsn_sc": hsn_sc,
            "desc": row.get("Description", ""),
            "uqc": row.get("UQC", "OTH-OTHERS"),
            "qty": _float(row.get("Total Quantity")),
            "txval": _float(row.get("Taxable Value")),
            "rt": _int(row.get("Rate", 0)),
            "iamt": _float(row.get("Integrated Tax Amount")),
            "camt": _float(row.get("Central Tax Amount")),
            "samt": _float(row.get("State/UT Tax Amount")),
            "csamt": _float(row.get("Cess Amount")),
        })
    if not data:
        return None
    return {"data": data}


def _build_doc_issue(rows):
    """Convert docs CSV rows to GSTN doc_issue structure."""
    if not rows:
        return None

    docs = []
    for i, row in enumerate(rows, 1):
        docs.append({
            "num": i,
            "from": row.get("Sr. No. From", ""),
            "to": row.get("Sr. No. To", ""),
            "totnum": _int(row.get("Total Number")),
            "cancel": _int(row.get("Cancelled")),
            "net_issue": _int(row.get("Total Number")) - _int(row.get("Cancelled")),
        })

    # doc_num 1 = Invoices for outward supply
    return {"doc_det": [{"doc_num": 1, "docs": docs}]}


def generate_json_for_state(state_folder, gstin, filing_period, seller_state_code):
    """
    Generate gstr1.json for a single state.

    Args:
        state_folder: Path to the state's output folder
        gstin: Seller GSTIN for this state (e.g. "07IFWPS9148C1ZK")
        filing_period: Filing period in MMYYYY format (e.g. "012026")
        seller_state_code: 2-digit state code (e.g. "07")

    Returns:
        Path to the generated JSON file
    """
    folder = Path(state_folder)

    # Read all CSVs
    b2b_rows = _read_csv(folder / "b2b,sez,de.csv")
    b2cs_rows = _read_csv(folder / "b2cs.csv")
    cdnr_rows = _read_csv(folder / "cdnr1.csv")
    hsn_b2b_rows = _read_csv(folder / "hsn(b2b).csv")
    hsn_b2c_rows = _read_csv(folder / "hsn(b2c).csv")
    docs_rows = _read_csv(folder / "docs.csv")

    # Build JSON structure
    gstr1 = {
        "gstin": gstin,
        "fp": filing_period,
    }

    b2b = _build_b2b(b2b_rows, seller_state_code)
    if b2b:
        gstr1["b2b"] = b2b

    b2cs = _build_b2cs(b2cs_rows, seller_state_code)
    if b2cs:
        gstr1["b2cs"] = b2cs

    cdnr = _build_cdnr(cdnr_rows, seller_state_code)
    if cdnr:
        gstr1["cdnr"] = cdnr

    hsn = _build_hsn(hsn_b2b_rows, hsn_b2c_rows)
    if hsn:
        gstr1["hsn"] = hsn

    doc_issue = _build_doc_issue(docs_rows)
    if doc_issue:
        gstr1["doc_issue"] = doc_issue

    # Write JSON
    out_path = folder / "gstr1.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(gstr1, f, indent=2, ensure_ascii=False)

    return out_path


def generate_all_json(folders, states_dict, config):
    """
    Generate gstr1.json for all states.

    Args:
        folders: {state_code: Path} from create_state_folders
        states_dict: {state_code: {"gstin": str, "name": str, ...}}
        config: config dict with project.month and project.year

    Returns:
        Number of JSON files generated
    """
    # Build filing period MMYYYY from config
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    month_str = month_map.get(config["project"]["month"].lower(), "01")
    year_str = config["project"]["year"]
    filing_period = f"{month_str}{year_str}"

    count = 0
    for code, info in sorted(states_dict.items()):
        folder = folders.get(code)
        if not folder or not folder.exists():
            continue

        out_path = generate_json_for_state(
            folder, info["gstin"], filing_period, code
        )
        count += 1
        print(f"  {code}-{info['name']}: gstr1.json generated")

    return count
