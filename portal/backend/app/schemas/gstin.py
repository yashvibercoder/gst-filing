"""GSTIN request/response schemas."""

from pydantic import BaseModel, field_validator
import re


class GSTINCreate(BaseModel):
    gstin: str

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v):
        v = v.strip().upper()
        if len(v) != 15:
            raise ValueError("GSTIN must be 15 characters")
        if not re.match(r"^\d{2}[A-Z0-9]{13}$", v):
            raise ValueError("Invalid GSTIN format")
        return v


class GSTINResponse(BaseModel):
    id: int
    gstin: str
    state_code: str
    state_name: str
    is_active: bool

    class Config:
        from_attributes = True


class GSTINUpdate(BaseModel):
    is_active: bool | None = None
