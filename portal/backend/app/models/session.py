"""Filing session database model."""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from ..database import Base


class FilingSession(Base):
    __tablename__ = "filing_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending/processing/completed/failed
    output_dir = Column(Text, nullable=True)
    states_count = Column(Integer, default=0)
    files_count = Column(Integer, default=0)
    validation_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
