from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.enums import UserRole


class UserBase(BaseModel):
    display_name: str
    # Make email optional for backward compatibility with tests that don't provide it.
    email: Optional[EmailStr] = None
    qr_code: Optional[str] = None
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    pin: Optional[str] = None  # Required for treasurer role


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    qr_code: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBalance(BaseModel):
    user: UserResponse
    balance_cents: int

    model_config = ConfigDict(from_attributes=True)