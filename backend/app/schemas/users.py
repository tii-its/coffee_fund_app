from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.enums import UserRole


class UserBase(BaseModel):
    display_name: str
    email: EmailStr  # required again
    qr_code: Optional[str] = None
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    pin: str  # Required for all users now


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    qr_code: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    pin: Optional[str] = None  # Optional PIN update


class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBalance(BaseModel):
    user: UserResponse
    balance_cents: int

    model_config = ConfigDict(from_attributes=True)


class UserPinVerificationRequest(BaseModel):
    user_id: UUID
    pin: str


class UserPinChangeRequest(BaseModel):
    user_id: UUID
    current_pin: str
    new_pin: str