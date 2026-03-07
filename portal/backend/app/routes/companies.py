"""Company profile endpoints."""

import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.company import Company
from ..schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse


def _make_slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-') or "company"

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.get("/", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.created_at).all()


@router.get("/active", response_model=CompanyResponse | None)
def get_active_company(db: Session = Depends(get_db)):
    return db.query(Company).filter(Company.is_active == True).first()


@router.post("/", response_model=CompanyResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(name=data.name, amazon_seller_id=data.amazon_seller_id, slug=_make_slug(data.name))
    # Auto-activate if it's the first company
    if db.query(Company).count() == 0:
        company.is_active = True
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")
    if data.name is not None:
        company.name = data.name
        company.slug = _make_slug(data.name)
    if data.amazon_seller_id is not None:
        company.amazon_seller_id = data.amazon_seller_id
    db.commit()
    db.refresh(company)
    return company


@router.post("/{company_id}/activate", response_model=CompanyResponse)
def activate_company(company_id: int, db: Session = Depends(get_db)):
    """Set this company as active, deactivating all others."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")
    db.query(Company).update({"is_active": False})
    company.is_active = True
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(404, "Company not found")
    db.delete(company)
    db.commit()
