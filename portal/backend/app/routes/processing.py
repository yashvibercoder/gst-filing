"""Processing endpoints — trigger GST pipeline and get results."""

import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_company
from ..config import settings
from ..models.company import Company
from ..models.session import FilingSession
from ..models.gstin import GSTIN
from ..models.upload import UploadLog
from ..schemas.session import SessionCreate, SessionResponse
from ..services.processing_bridge import run_pipeline

router = APIRouter(prefix="/api/processing", tags=["Processing"])


@router.post("/run", response_model=SessionResponse)
def start_processing(
    data: SessionCreate,
    company: Company = Depends(get_company),
    db: Session = Depends(get_db),
):
    """Run the GST pipeline for the active company and return session with results."""
    session = FilingSession(company_id=company.id, month=data.month, year=data.year, status="processing")
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        # Query active GSTINs for this company only
        all_gstins = db.query(GSTIN).filter(GSTIN.company_id == company.id).all()
        active_states = None
        if all_gstins:
            active_states = [g.state_code for g in all_gstins if g.is_active]

        company_slug = company.slug or "default"
        amazon_seller_id = company.amazon_seller_id

        result = run_pipeline(
            month=data.month, year=data.year, session_id=session.id,
            active_states=active_states, amazon_seller_id=amazon_seller_id,
            company_slug=company_slug,
        )
        session.status = "completed"
        session.output_dir = str(result["output_dir"])
        session.states_count = result["states_count"]
        session.files_count = result["files_count"]
        session.validation_summary = json.dumps(result["validation"])
        session.completed_at = datetime.now()

        # Clear this company's uploaded files so next run starts fresh
        upload_dir = Path(settings.upload_dir)
        for log in db.query(UploadLog).filter(UploadLog.company_id == company.id).all():
            stored = upload_dir / log.stored_filename
            if stored.exists():
                stored.unlink()
            db.delete(log)
    except Exception as e:
        session.status = "failed"
        session.error_message = str(e)
        session.completed_at = datetime.now()

    db.commit()
    db.refresh(session)
    return session


@router.get("/status/{session_id}", response_model=SessionResponse)
def get_status(session_id: int, company: Company = Depends(get_company), db: Session = Depends(get_db)):
    session = db.query(FilingSession).filter(
        FilingSession.id == session_id,
        FilingSession.company_id == company.id,
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.get("/history", response_model=list[SessionResponse])
def list_sessions(company: Company = Depends(get_company), db: Session = Depends(get_db)):
    return (
        db.query(FilingSession)
        .filter(FilingSession.company_id == company.id)
        .order_by(FilingSession.created_at.desc())
        .all()
    )
