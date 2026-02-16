"""Results endpoints — browse and download generated output."""

import csv
import io
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
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
            states.append({"code": code, "name": name, "files": files})
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
