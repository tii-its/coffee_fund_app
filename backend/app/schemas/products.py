from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ProductBase(BaseModel):
    name: str
    price_cents: int
    icon: Optional[str] = '☕'
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price_cents: Optional[int] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserConsumptionStat(BaseModel):
    """User consumption statistics for a product"""
    user_id: UUID
    display_name: str
    total_qty: int
    total_amount_cents: int

    model_config = ConfigDict(from_attributes=True)


class ProductConsumptionStats(BaseModel):
    """Product with its top consumers"""
    product: ProductResponse
    top_consumers: List[UserConsumptionStat]

    model_config = ConfigDict(from_attributes=True)