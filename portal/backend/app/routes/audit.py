"""Audit endpoints — upload templates, run audit, view report."""

import re
import shutil
import subprocess
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse

from ..config import settings

router = APIRouter(prefix="/api/audit", tags=["Audit"])

AUDIT_DIR = settings.project_root / "audit"
TEMPLATES_DIR = AUDIT_DIR / "templates"
OUTPUT_DIR = AUDIT_DIR / "output"
REPORTS_DIR = AUDIT_DIR / "reports"


@router.post("/upload-templates")
async def upload_templates(files: list[UploadFile] = File(...)):
    """Upload previous month's template CSVs for comparison."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        if not f.filename:
            continue
        dest = TEMPLATES_DIR / f.filename
        content = await f.read()
        dest.write_bytes(content)
        saved.append(f.filename)

    return {"uploaded": saved, "count": len(saved)}


@router.get("/templates")
def list_templates():
    """List uploaded template files."""
    if not TEMPLATES_DIR.exists():
        return []
    return [f.name for f in sorted(TEMPLATES_DIR.glob("*.csv"))]


@router.delete("/templates")
def clear_templates():
    """Remove all template files."""
    if TEMPLATES_DIR.exists():
        shutil.rmtree(TEMPLATES_DIR)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    return {"status": "cleared"}


@router.post("/run")
def run_audit(state_code: str = "07"):
    """Copy state output to audit/output and run the audit script."""
    # Find the state folder — search newest month subfolders first (output/MM_YYYY/),
    # then fall back to the root output/ for legacy runs
    output_root = settings.project_root / "output"
    state_folder = None

    # Collect month dirs from: output/MM_YYYY/ AND output/{company}/{MM_YYYY}/
    raw_month_dirs = [d for d in output_root.iterdir() if d.is_dir() and re.match(r'^\d{2}_\d{4}$', d.name)]
    for company_dir in output_root.iterdir():
        if company_dir.is_dir() and not re.match(r'^\d{2}_\d{4}$', company_dir.name):
            for sub in company_dir.iterdir():
                if sub.is_dir() and re.match(r'^\d{2}_\d{4}$', sub.name):
                    raw_month_dirs.append(sub)

    month_dirs = sorted(
        raw_month_dirs,
        key=lambda d: (int(d.name[3:]), int(d.name[:2])),
        reverse=True
    )
    search_dirs = month_dirs + [output_root]

    for search_dir in search_dirs:
        for folder in search_dir.iterdir():
            if folder.is_dir() and folder.name.startswith(state_code + "-"):
                state_folder = folder
                break
        if state_folder:
            break

    if not state_folder:
        raise HTTPException(404, f"No output found for state {state_code}")

    # Copy CSVs to audit/output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Clear previous
    for f in OUTPUT_DIR.glob("*.csv"):
        f.unlink()
    for csv_file in state_folder.glob("*.csv"):
        shutil.copy2(csv_file, OUTPUT_DIR / csv_file.name)

    # Ensure reports dir exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Run audit script
    audit_script = AUDIT_DIR / "run_audit.py"
    if not audit_script.exists():
        raise HTTPException(404, "Audit script not found at audit/run_audit.py")

    result = subprocess.run(
        ["python", str(audit_script)],
        cwd=str(AUDIT_DIR),
        capture_output=True,
        text=True,
        timeout=60,
    )

    report_path = REPORTS_DIR / "audit_report.md"
    has_report = report_path.exists()

    return {
        "status": "completed" if result.returncode == 0 else "error",
        "stdout": result.stdout[-2000:] if result.stdout else "",
        "stderr": result.stderr[-1000:] if result.stderr else "",
        "has_report": has_report,
    }


@router.get("/report")
def get_report():
    """Return the audit report markdown content."""
    report_path = REPORTS_DIR / "audit_report.md"
    if not report_path.exists():
        raise HTTPException(404, "No audit report found. Run the audit first.")

    content = report_path.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/markdown")
