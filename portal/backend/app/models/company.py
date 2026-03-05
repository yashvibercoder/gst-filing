"""Company profile database model."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from ..database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=True)               # URL/folder-safe name e.g. "acme-traders"
    amazon_seller_id = Column(String(50), nullable=True)   # e.g. A3SZBDZ05A1P39
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
