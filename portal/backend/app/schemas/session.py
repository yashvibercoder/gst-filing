"""Filing session request/response schemas."""

from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    month: int
    year: int


class SessionResponse(BaseModel):
    id: int
    month: int
    year: int
    status: str
    states_count: int
    files_count: int
    validation_summary: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
