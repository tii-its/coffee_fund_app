from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from app.schemas.users import UserResponse
from app.schemas.products import ProductResponse


class ConsumptionBase(BaseModel):
    user_id: UUID
    product_id: UUID
    qty: int


class ConsumptionCreate(ConsumptionBase):
    pass


class ConsumptionResponse(ConsumptionBase):
    id: UUID
    unit_price_cents: int
    amount_cents: int
    at: datetime
    created_by: UUID
    user: UserResponse
    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)