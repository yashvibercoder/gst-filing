"""Processing endpoints — trigger GST pipeline and get results."""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.session import FilingSession
from ..schemas.session import SessionCreate, SessionResponse
from ..services.processing_bridge import run_pipeline

router = APIRouter(prefix="/api/processing", tags=["Processing"])


@router.post("/run", response_model=SessionResponse)
def start_processing(data: SessionCreate, db: Session = Depends(get_db)):
    """Run the GST pipeline and return session with results."""
    session = FilingSession(month=data.month, year=data.year, status="processing")
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        result = run_pipeline()
        session.status = "completed"
        session.output_dir = str(result["output_dir"])
        session.states_count = result["states_count"]
        session.files_count = result["files_count"]
        session.validation_summary = json.dumps(result["validation"])
        session.completed_at = datetime.now()
    except Exception as e:
        session.status = "failed"
        session.error_message = str(e)
        session.completed_at = datetime.now()

    db.commit()
    db.refresh(session)
    return session


@router.get("/status/{session_id}", response_model=SessionResponse)
def get_status(session_id: int, db: Session = Depends(get_db)):
    session = db.query(FilingSession).filter(FilingSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.get("/history", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(FilingSession).order_by(FilingSession.created_at.desc()).all()
