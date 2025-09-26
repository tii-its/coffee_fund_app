from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProductBase(BaseModel):
    name: str
    price_cents: int
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price_cents: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True