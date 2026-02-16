"""Upload log database model."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func

from ..database import Base


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("filing_sessions.id"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    platform = Column(String(20), nullable=True)  # flipkart/amazon/meesho/einvoice
    file_size = Column(BigInteger, default=0)
    uploaded_at = Column(DateTime, server_default=func.now())
