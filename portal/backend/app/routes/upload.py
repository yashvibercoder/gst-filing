"""File upload endpoints."""

import fnmatch
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..models.upload import UploadLog
from ..schemas.upload import UploadResponse

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
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Generate unique stored filename
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "xlsx"
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = settings.upload_dir / stored_name

    # Save file
    content = await file.read()
    with open(stored_path, "wb") as f:
        f.write(content)

    # Detect platform
    platform = detect_platform(file.filename)

    # Log upload
    log = UploadLog(
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
def list_uploads(db: Session = Depends(get_db)):
    return db.query(UploadLog).order_by(UploadLog.uploaded_at.desc()).all()


@router.delete("/{upload_id}", status_code=204)
def delete_upload(upload_id: int, db: Session = Depends(get_db)):
    log = db.query(UploadLog).filter(UploadLog.id == upload_id).first()
    if not log:
        raise HTTPException(404, "Upload not found")

    # Delete stored file
    stored_path = settings.upload_dir / log.stored_filename
    if stored_path.exists():
        stored_path.unlink()

    db.delete(log)
    db.commit()
