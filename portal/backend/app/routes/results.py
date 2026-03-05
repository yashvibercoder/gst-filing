"""Results endpoints — browse and download generated output."""

import csv
import io
import json
import zipfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import FilingSession

router = APIRouter(prefix="/api/results", tags=["Results"])


@router.get("/{session_id}/states")
def list_states(session_id: int, db: Session = Depends(get_db)):
    """List states with generated output for a session."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found or no output")

    output_dir = Path(session.output_dir)
    states = []
    for folder in sorted(output_dir.iterdir()):
        if folder.is_dir() and "-" in folder.name:
            code, name = folder.name.split("-", 1)
            files = [f.name for f in sorted(folder.glob("*.csv"))]
            json_files = [f.name for f in sorted(folder.glob("*.json"))]
            states.append({"code": code, "name": name, "files": files, "json_files": json_files})
    return states


@router.get("/{session_id}/states/{state_code}/files/{filename}")
def get_file_data(session_id: int, state_code: str, filename: str,
                  db: Session = Depends(get_db)):
    """Return CSV file contents as JSON for the Review table."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found")

    output_dir = Path(session.output_dir)
    # Find the state folder
    state_folder = None
    for folder in output_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(state_code + "-"):
            state_folder = folder
            break

    if not state_folder:
        raise HTTPException(404, f"State {state_code} not found")

    csv_path = state_folder / filename
    if not csv_path.exists():
        raise HTTPException(404, f"File {filename} not found")

    # Read CSV and return as JSON
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    return {"columns": columns, "rows": rows, "total": len(rows)}


@router.get("/{session_id}/states/{state_code}/files/{filename}/download")
def download_file(session_id: int, state_code: str, filename: str,
                  db: Session = Depends(get_db)):
    """Download a CSV file."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found")

    output_dir = Path(session.output_dir)
    state_folder = None
    for folder in output_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(state_code + "-"):
            state_folder = folder
            break

    if not state_folder:
        raise HTTPException(404, f"State {state_code} not found")

    csv_path = state_folder / filename
    if not csv_path.exists():
        raise HTTPException(404, f"File {filename} not found")

    return FileResponse(csv_path, filename=filename, media_type="text/csv")


@router.get("/{session_id}/validation")
def get_validation_report(session_id: int, db: Session = Depends(get_db)):
    """Parse validation_checks.csv and return as structured JSON."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found")

    report_path = Path(session.output_dir) / "validation_checks.csv"
    if not report_path.exists():
        raise HTTPException(404, "Validation report not found")

    checks = []
    counts = {"pass": 0, "fail": 0, "warn": 0}
    with open(report_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get("status", "").upper()
            checks.append({
                "check": row.get("check", ""),
                "status": status,
                "state": row.get("state", ""),
                "details": row.get("detail", ""),
            })
            if status == "PASS":
                counts["pass"] += 1
            elif status == "FAIL":
                counts["fail"] += 1
            elif status == "WARN":
                counts["warn"] += 1

    return {"summary": counts, "checks": checks}


@router.get("/{session_id}/states/{state_code}/json")
def get_state_json(session_id: int, state_code: str,
                   db: Session = Depends(get_db)):
    """Return gstr1.json content for a state."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found")

    output_dir = Path(session.output_dir)
    state_folder = None
    for folder in output_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(state_code + "-"):
            state_folder = folder
            break

    if not state_folder:
        raise HTTPException(404, f"State {state_code} not found")

    json_path = state_folder / "gstr1.json"
    if not json_path.exists():
        raise HTTPException(404, "gstr1.json not found for this state")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _safe_float(val) -> float:
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0.0


def _section_totals(csv_path: Path, state_code: str) -> dict:
    """Read a CSV file and compute row count + CGST/SGST/IGST/CESS totals."""
    rows_data = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows_data = list(reader)
    except Exception:
        return {"rows": 0, "igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}

    n = len(rows_data)
    if n == 0:
        return {"rows": 0, "igst": 0.0, "cgst": 0.0, "sgst": 0.0, "cess": 0.0}

    igst = cgst = sgst = cess = 0.0
    first = rows_data[0]

    if "Integrated Tax Amount" in first:
        # HSN files — tax columns are explicit
        for row in rows_data:
            igst += _safe_float(row.get("Integrated Tax Amount"))
            cgst += _safe_float(row.get("Central Tax Amount"))
            sgst += _safe_float(row.get("State/UT Tax Amount"))
            cess += _safe_float(row.get("Cess Amount"))
    elif "Taxable Value" in first and "Rate" in first:
        # B2B / B2CS / CDNR / ECO — derive tax from Taxable Value × Rate, split by PoS
        has_pos = "Place Of Supply" in first
        for row in rows_data:
            txval = _safe_float(row.get("Taxable Value"))
            rate = _safe_float(row.get("Rate"))
            cess += _safe_float(row.get("Cess Amount"))
            tax = txval * rate / 100
            if has_pos:
                pos = (row.get("Place Of Supply") or "")[:2]
                if pos == state_code:
                    cgst += tax / 2
                    sgst += tax / 2
                else:
                    igst += tax
            else:
                igst += tax

    return {
        "rows": n,
        "igst": round(igst, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "cess": round(cess, 2),
    }


SECTION_DEFS = [
    {"key": "b2b",     "file": "b2b,sez,de.csv", "label": "B2B, SEZ, DE Invoices",              "section_code": "4A, 4B, 6B, 6C"},
    {"key": "b2cs",    "file": "b2cs.csv",        "label": "B2C (Small) Details",                "section_code": "7"},
    {"key": "cdnr",    "file": "cdnr1.csv",       "label": "Credit / Debit Notes (B2B)",         "section_code": "9B"},
    {"key": "eco",     "file": "eco.csv",         "label": "Supplies through E-Commerce Operator","section_code": "14"},
    {"key": "hsn_b2b", "file": "hsn(b2b).csv",   "label": "HSN-wise Summary (B2B)",             "section_code": "12"},
    {"key": "hsn_b2c", "file": "hsn(b2c).csv",   "label": "HSN-wise Summary (B2C)",             "section_code": "12"},
    {"key": "docs",    "file": "docs.csv",        "label": "Documents Issued",                   "section_code": "13"},
]


@router.get("/{session_id}/summary")
def get_summary(session_id: int, db: Session = Depends(get_db)):
    """Per-state, per-section summary: row counts and tax totals (GSTN Offline Tool style)."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found or no output")

    output_dir = Path(session.output_dir)
    states_out = []

    for folder in sorted(output_dir.iterdir()):
        if not folder.is_dir() or "-" not in folder.name:
            continue
        code, name = folder.name.split("-", 1)
        sections = []
        for defn in SECTION_DEFS:
            csv_path = folder / defn["file"]
            if not csv_path.exists():
                continue
            totals = _section_totals(csv_path, code)
            sections.append({
                "key":          defn["key"],
                "label":        defn["label"],
                "section_code": defn["section_code"],
                **totals,
            })
        if sections:
            states_out.append({"code": code, "name": name, "sections": sections})

    return {"states": states_out}


@router.get("/{session_id}/analytics")
def get_analytics(session_id: int, db: Session = Depends(get_db)):
    """Aggregate tax analytics from all state gstr1.json files."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found or no output")

    output_dir = Path(session.output_dir)
    states = []
    rate_totals = {}  # rate -> {taxable_value, tax}

    total_taxable = 0.0
    total_igst = 0.0
    total_cgst = 0.0
    total_sgst = 0.0

    for folder in sorted(output_dir.iterdir()):
        if not folder.is_dir() or "-" not in folder.name:
            continue
        json_path = folder / "gstr1.json"
        if not json_path.exists():
            continue

        code, name = folder.name.split("-", 1)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        st_txval = 0.0
        st_igst = 0.0
        st_cgst = 0.0
        st_sgst = 0.0
        sections = {"b2b": 0, "b2cs": 0, "cdnr": 0}

        # B2B: list of ctin groups -> inv list -> itms list
        for ctin_group in data.get("b2b", []):
            for inv in ctin_group.get("inv", []):
                sections["b2b"] += 1
                for itm in inv.get("itms", []):
                    det = itm.get("itm_det", {})
                    txval = det.get("txval", 0)
                    iamt = det.get("iamt", 0)
                    camt = det.get("camt", 0)
                    samt = det.get("samt", 0)
                    rt = det.get("rt", 0)
                    st_txval += txval
                    st_igst += iamt
                    st_cgst += camt
                    st_sgst += samt
                    rate_totals.setdefault(rt, {"taxable_value": 0.0, "tax": 0.0})
                    rate_totals[rt]["taxable_value"] += txval
                    rate_totals[rt]["tax"] += iamt + camt + samt

        # B2CS: flat list with txval, iamt, camt, samt
        for entry in data.get("b2cs", []):
            sections["b2cs"] += 1
            txval = entry.get("txval", 0)
            iamt = entry.get("iamt", 0)
            camt = entry.get("camt", 0)
            samt = entry.get("samt", 0)
            rt = entry.get("rt", 0)
            st_txval += txval
            st_igst += iamt
            st_cgst += camt
            st_sgst += samt
            rate_totals.setdefault(rt, {"taxable_value": 0.0, "tax": 0.0})
            rate_totals[rt]["taxable_value"] += txval
            rate_totals[rt]["tax"] += iamt + camt + samt

        # CDNR: list of ctin groups -> nt list -> itms list
        for ctin_group in data.get("cdnr", []):
            for nt in ctin_group.get("nt", []):
                sections["cdnr"] += 1
                for itm in nt.get("itms", []):
                    det = itm.get("itm_det", {})
                    txval = det.get("txval", 0)
                    iamt = det.get("iamt", 0)
                    camt = det.get("camt", 0)
                    samt = det.get("samt", 0)
                    rt = det.get("rt", 0)
                    st_txval += txval
                    st_igst += iamt
                    st_cgst += camt
                    st_sgst += samt
                    rate_totals.setdefault(rt, {"taxable_value": 0.0, "tax": 0.0})
                    rate_totals[rt]["taxable_value"] += txval
                    rate_totals[rt]["tax"] += iamt + camt + samt

        invoice_count = sections["b2b"] + sections["b2cs"] + sections["cdnr"]
        state_tax = round(st_igst + st_cgst + st_sgst, 2)
        states.append({
            "code": code,
            "name": name,
            "taxable_value": round(st_txval, 2),
            "igst": round(st_igst, 2),
            "cgst": round(st_cgst, 2),
            "sgst": round(st_sgst, 2),
            "total_tax": state_tax,
            "invoice_count": invoice_count,
            "sections": sections,
        })

        total_taxable += st_txval
        total_igst += st_igst
        total_cgst += st_cgst
        total_sgst += st_sgst

    rate_breakdown = sorted(
        [{"rate": int(rt), "taxable_value": round(v["taxable_value"], 2), "tax": round(v["tax"], 2)}
         for rt, v in rate_totals.items()],
        key=lambda x: x["rate"],
    )

    return {
        "total_taxable_value": round(total_taxable, 2),
        "total_igst": round(total_igst, 2),
        "total_cgst": round(total_cgst, 2),
        "total_sgst": round(total_sgst, 2),
        "total_tax": round(total_igst + total_cgst + total_sgst, 2),
        "states": states,
        "rate_breakdown": rate_breakdown,
    }


@router.get("/{session_id}/download")
def download_session_zip(session_id: int, db: Session = Depends(get_db)):
    """Download all output files for a session as a ZIP archive."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found or no output")

    output_dir = Path(session.output_dir)
    if not output_dir.exists():
        raise HTTPException(404, "Output directory not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in output_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(output_dir))
    buf.seek(0)

    month_year = output_dir.name  # e.g. "01_2026"
    zip_name = f"GST_Filing_{month_year}_session{session_id}.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@router.get("/{session_id}/states/{state_code}/json/download")
def download_state_json(session_id: int, state_code: str,
                        db: Session = Depends(get_db)):
    """Download gstr1.json for a state."""
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session or not session.output_dir:
        raise HTTPException(404, "Session not found")

    output_dir = Path(session.output_dir)
    state_folder = None
    for folder in output_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(state_code + "-"):
            state_folder = folder
            break

    if not state_folder:
        raise HTTPException(404, f"State {state_code} not found")

    json_path = state_folder / "gstr1.json"
    if not json_path.exists():
        raise HTTPException(404, "gstr1.json not found")

    return FileResponse(
        json_path,
        filename=f"gstr1_{state_code}.json",
        media_type="application/json",
    )
