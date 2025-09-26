from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.enums import UserRole


class UserBase(BaseModel):
    display_name: str
    qr_code: Optional[str] = None
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    qr_code: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserBalance(BaseModel):
    user: UserResponse
    balance_cents: int

    class Config:
        from_attributes = True