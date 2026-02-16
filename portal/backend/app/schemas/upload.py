"""Upload request/response schemas."""

from pydantic import BaseModel
from datetime import datetime


class UploadResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    platform: str | None
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
