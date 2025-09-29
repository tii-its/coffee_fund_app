from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models import User
from app.schemas import UserBalance, UserCreate, UserResponse, UserUpdate, UserPinVerificationRequest, UserPinChangeRequest
from app.services.audit import AuditService
from app.services.balance import BalanceService
from app.services.qr_code import QRCodeService
from app.services.pin import PinService
from app.core.enums import UserRole

router = APIRouter(prefix="/users", tags=["users"])

"""User management endpoints.

Refactored: Removed global Admin/Treasurer PIN concept. All authentication now
relies on per-user PINs. User creation always requires a per-user PIN (hashed
server-side). Privileged actions (future enhancement) should verify the actor's
own PIN; for now we only log actor_id for audit trail.
"""


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    creator_id: Optional[UUID] = Query(None, description="ID of the user creating this user")
):
    """Create a new user.

    Requirements:
    - Email must be unique.
    - Per-user PIN is mandatory (already enforced by schema).
    """
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Hash user PIN
    user_data = user.model_dump(exclude={'pin'})
    user_data['pin_hash'] = PinService.hash_pin(user.pin)
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if creator_id:
        AuditService.log_action(
            db=db,
            actor_id=creator_id,
            action="create",
            entity="user",
            entity_id=db_user.id,
            meta_data={"display_name": user.display_name, "email": str(getattr(user, 'email', '')), "role": user.role.value}
        )

    return UserResponse.model_validate(db_user)


@router.get("/", response_model=list[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all users"""
    query = db.query(User)
    if active_only:
        query = query.filter(User.is_active == True)

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    actor_id: Optional[UUID] = Query(None, description="ID of the user performing the update")
):
    """Update a user.

    NOTE: Actor authorization & PIN verification to be added in a future
    enhancement; currently any caller can update. Only PIN changes require
    providing a new 'pin' value inside user_update.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    if 'pin' in update_data:
        new_pin = update_data.pop('pin')
        if new_pin:
            user.pin_hash = PinService.hash_pin(new_pin)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    if actor_id:
        AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="update",
            entity="user",
            entity_id=user.id,
            meta_data=update_data
        )

    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    actor_id: Optional[UUID] = Query(None, description="ID of the user performing the deletion")
):
    """Soft delete a user.

    NOTE: Actor authorization & PIN verification will be added later.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)

    if actor_id:
        AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="delete",
            entity="user",
            entity_id=user.id,
            meta_data={"display_name": user.display_name, "soft_delete": True}
        )

    return {"message": "User deleted successfully"}


# Removed legacy global /verify-pin endpoint (deprecated)


@router.post("/verify-user-pin")
def verify_user_pin(pin_request: UserPinVerificationRequest, db: Session = Depends(get_db)):
    """Verify a specific user's PIN"""
    if not PinService.verify_user_pin(pin_request.user_id, pin_request.pin, db):
        raise HTTPException(status_code=403, detail="Invalid user PIN")
    
    return {"message": "User PIN verified successfully"}


# Removed legacy global /change-pin endpoint (deprecated)


@router.post("/change-user-pin")
def change_user_pin(
    pin_change: UserPinChangeRequest,
    db: Session = Depends(get_db),
    actor_id: Optional[UUID] = Query(None, description="ID of the user changing the PIN")
):
    """Change a specific user's PIN (requires current PIN)"""
    if not PinService.change_user_pin(pin_change.user_id, pin_change.current_pin, pin_change.new_pin, db):
        raise HTTPException(status_code=403, detail="Invalid current PIN")
    
    # Log the action for audit purposes
    if actor_id:
        AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="change_user_pin",
            entity="user", 
            entity_id=pin_change.user_id,
            meta_data={"operation": "user_pin_change"}
        )
    
    return {"message": "User PIN changed successfully"}


@router.get("/{user_id}/balance", response_model=UserBalance)
def get_user_balance(user_id: UUID, db: Session = Depends(get_db)):
    """Get user's current balance"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    balance = BalanceService.get_user_balance(db, str(user_id))
    return UserBalance(user=UserResponse.model_validate(user), balance_cents=balance)


@router.get("/{user_id}/qr-code")
def get_user_qr_code(user_id: UUID, db: Session = Depends(get_db)):
    """Generate QR code for user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    qr_code = QRCodeService.generate_user_qr_code(str(user_id))
    return {"qr_code": qr_code}


@router.get("/balances/all", response_model=list[UserBalance])
def get_all_balances(db: Session = Depends(get_db)):
    """Get balances for all users"""
    return BalanceService.get_all_user_balances(db)


@router.get("/balances/below-threshold", response_model=list[UserBalance])
def get_users_below_threshold(
    threshold_cents: int = Query(1000, description="Threshold in cents"),
    db: Session = Depends(get_db)
):
    """Get users with balance below threshold"""
    return BalanceService.get_users_below_threshold(db, threshold_cents)


@router.get("/balances/above-threshold", response_model=list[UserBalance])
def get_users_above_threshold(
    threshold_cents: int = Query(1000, description="Threshold in cents"),
    db: Session = Depends(get_db)
):
    """Get users with balance above or equal to threshold"""
    return BalanceService.get_users_above_threshold(db, threshold_cents)
