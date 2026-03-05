"""GSTIN management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_company
from ..models.company import Company
from ..models.gstin import GSTIN
from ..schemas.gstin import GSTINCreate, GSTINResponse, GSTINUpdate

router = APIRouter(prefix="/api/gstins", tags=["GSTINs"])


@router.get("/", response_model=list[GSTINResponse])
def list_gstins(company: Company = Depends(get_company), db: Session = Depends(get_db)):
    return db.query(GSTIN).filter(GSTIN.company_id == company.id).order_by(GSTIN.state_code).all()


@router.post("/", response_model=GSTINResponse, status_code=201)
def add_gstin(data: GSTINCreate, company: Company = Depends(get_company), db: Session = Depends(get_db)):
    existing = db.query(GSTIN).filter(GSTIN.gstin == data.gstin, GSTIN.company_id == company.id).first()
    if existing:
        raise HTTPException(400, "GSTIN already exists for this company")

    state_code, state_name = GSTIN.detect_state(data.gstin)
    gstin = GSTIN(
        company_id=company.id,
        gstin=data.gstin,
        state_code=state_code,
        state_name=state_name,
        portal_username=data.portal_username,
        portal_password=data.portal_password,
    )
    db.add(gstin)
    db.commit()
    db.refresh(gstin)
    return gstin


@router.put("/{gstin_id}", response_model=GSTINResponse)
def update_gstin(gstin_id: int, data: GSTINUpdate, company: Company = Depends(get_company), db: Session = Depends(get_db)):
    gstin = db.query(GSTIN).filter(GSTIN.id == gstin_id, GSTIN.company_id == company.id).first()
    if not gstin:
        raise HTTPException(404, "GSTIN not found")

    if data.is_active is not None:
        gstin.is_active = data.is_active
    if data.portal_username is not None:
        gstin.portal_username = data.portal_username
    if data.portal_password is not None:
        gstin.portal_password = data.portal_password

    db.commit()
    db.refresh(gstin)
    return gstin


@router.delete("/{gstin_id}", status_code=204)
def delete_gstin(gstin_id: int, company: Company = Depends(get_company), db: Session = Depends(get_db)):
    gstin = db.query(GSTIN).filter(GSTIN.id == gstin_id, GSTIN.company_id == company.id).first()
    if not gstin:
        raise HTTPException(404, "GSTIN not found")
    db.delete(gstin)
    db.commit()
