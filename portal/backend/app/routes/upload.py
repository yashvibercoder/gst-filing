"""File upload endpoints."""

import fnmatch
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_company
from ..config import settings
from ..models.company import Company
from ..models.upload import UploadLog
from ..schemas.upload import UploadResponse

VALID_PLATFORMS = {"flipkart", "amazon", "meesho", "einvoice", "offline_b2b"}


class PlatformUpdate(BaseModel):
    platform: str | None

router = APIRouter(prefix="/api/upload", tags=["Upload"])


def detect_platform(filename: str) -> str | None:
    """Auto-detect platform from filename using config patterns."""
    gst_config = settings.load_gst_config()
    patterns = gst_config.get("file_patterns", {})
    for platform, pattern in patterns.items():
        if fnmatch.fnmatch(filename, pattern):
            return platform
    return None


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    company: Company = Depends(get_company),
    db: Session = Depends(get_db),
):
    stored_name = file.filename
    stored_path = settings.upload_dir / stored_name

    content = await file.read()
    with open(stored_path, "wb") as f:
        f.write(content)

    platform = detect_platform(file.filename)

    log = UploadLog(
        company_id=company.id,
        original_filename=file.filename,
        stored_filename=stored_name,
        platform=platform,
        file_size=len(content),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/", response_model=list[UploadResponse])
def list_uploads(company: Company = Depends(get_company), db: Session = Depends(get_db)):
    return (
        db.query(UploadLog)
        .filter(UploadLog.company_id == company.id)
        .order_by(UploadLog.uploaded_at.desc())
        .all()
    )


@router.patch("/{upload_id}", response_model=UploadResponse)
def update_platform(upload_id: int, data: PlatformUpdate, company: Company = Depends(get_company), db: Session = Depends(get_db)):
    """Manually set or clear the platform tag for an uploaded file."""
    log = db.query(UploadLog).filter(UploadLog.id == upload_id, UploadLog.company_id == company.id).first()
    if not log:
        raise HTTPException(404, "Upload not found")
    if data.platform is not None and data.platform not in VALID_PLATFORMS:
        raise HTTPException(400, f"Invalid platform. Must be one of: {', '.join(sorted(VALID_PLATFORMS))}")
    log.platform = data.platform
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{upload_id}", status_code=204)
def delete_upload(upload_id: int, company: Company = Depends(get_company), db: Session = Depends(get_db)):
    log = db.query(UploadLog).filter(UploadLog.id == upload_id, UploadLog.company_id == company.id).first()
    if not log:
        raise HTTPException(404, "Upload not found")

    # Delete stored file
    stored_path = settings.upload_dir / log.stored_filename
    if stored_path.exists():
        stored_path.unlink()

    db.delete(log)
    db.commit()
