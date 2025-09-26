from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.enums import MoneyMoveType, MoneyMoveStatus
from app.schemas.users import UserResponse


class MoneyMoveBase(BaseModel):
    type: MoneyMoveType
    user_id: UUID
    amount_cents: int
    note: Optional[str] = None


class MoneyMoveCreate(MoneyMoveBase):
    pass


class MoneyMoveUpdate(BaseModel):
    status: MoneyMoveStatus


class MoneyMoveResponse(MoneyMoveBase):
    id: UUID
    created_at: datetime
    created_by: UUID
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[UUID] = None
    status: MoneyMoveStatus
    user: UserResponse

    class Config:
        from_attributes = True