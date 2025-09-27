from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class StockPurchaseBase(BaseModel):
    item_name: str
    supplier: Optional[str] = None
    quantity: int
    unit_price_cents: int
    total_amount_cents: int
    purchase_date: datetime
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class StockPurchaseCreate(StockPurchaseBase):
    pass


class StockPurchaseUpdate(BaseModel):
    item_name: Optional[str] = None
    supplier: Optional[str] = None
    quantity: Optional[int] = None
    unit_price_cents: Optional[int] = None
    total_amount_cents: Optional[int] = None
    purchase_date: Optional[datetime] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    is_cash_out_processed: Optional[bool] = None


class StockPurchaseResponse(StockPurchaseBase):
    id: UUID
    is_cash_out_processed: bool
    created_at: datetime
    created_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


class StockPurchaseWithCreator(StockPurchaseResponse):
    creator: dict  # Simplified creator info
    
    model_config = ConfigDict(from_attributes=True)