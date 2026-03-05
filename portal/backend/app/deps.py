"""Shared FastAPI dependencies."""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .models.company import Company


async def get_company(
    x_company_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Company:
    """Read X-Company-ID header and return the matching Company row."""
    if x_company_id is None:
        raise HTTPException(status_code=401, detail="X-Company-ID header required")
    company = db.query(Company).filter(Company.id == x_company_id).first()
    if not company:
        raise HTTPException(status_code=401, detail="Invalid company")
    return company
