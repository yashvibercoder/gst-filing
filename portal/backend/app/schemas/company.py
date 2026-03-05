"""Company request/response schemas."""

from pydantic import BaseModel
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    amazon_seller_id: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    amazon_seller_id: str | None = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    amazon_seller_id: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
