from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models import User
from app.schemas import UserBalance, UserCreate, UserResponse, UserUpdate
from app.services.audit import AuditService
from app.services.balance import BalanceService
from app.services.qr_code import QRCodeService
from app.services.pin import PinService
from app.core.enums import UserRole

router = APIRouter(prefix="/users", tags=["users"])


# PIN verification schemas
class PinVerificationRequest(BaseModel):
    pin: str

class PinChangeRequest(BaseModel):
    current_pin: str
    new_pin: str


@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    creator_id: Optional[UUID] = Query(None, description="ID of the user creating this user")
):
    """Create a new user"""
    # Check if user with this display name already exists
    existing_user = db.query(User).filter(User.display_name == user.display_name).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this display name already exists")

    # Create new user
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Log action
    if creator_id:
        AuditService.log_action(
            db=db,
            actor_id=creator_id,
            action="create",
            entity="user",
            entity_id=db_user.id,
            meta_data={"display_name": user.display_name, "role": user.role.value}
        )

    return db_user


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
    actor_id: Optional[UUID] = Query(None, description="ID of the user performing the update"),
    pin: str = Body(..., description="PIN for treasurer verification", embed=True)
):
    """Update a user (requires PIN verification)"""
    # Verify PIN for treasurer operations
    if not PinService.verify_pin(pin):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Log action
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
    actor_id: Optional[UUID] = Query(None, description="ID of the user performing the deletion"),
    pin: str = Body(..., description="PIN for treasurer verification", embed=True)
):
    """Delete a user (requires PIN verification)"""
    # Verify PIN for treasurer operations
    if not PinService.verify_pin(pin):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Soft delete by setting is_active to False
    user.is_active = False
    db.commit()
    db.refresh(user)

    # Log action
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


@router.post("/verify-pin")
def verify_pin(pin_request: PinVerificationRequest):
    """Verify PIN for treasurer operations"""
    if not PinService.verify_pin(pin_request.pin):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    
    return {"message": "PIN verified successfully"}


@router.post("/change-pin")
def change_pin(
    pin_change: PinChangeRequest,
    db: Session = Depends(get_db),
    actor_id: Optional[UUID] = Query(None, description="ID of the user changing the PIN")
):
    """Change the treasurer PIN (requires current PIN)"""
    # Verify current PIN
    if not PinService.verify_pin(pin_change.current_pin):
        raise HTTPException(status_code=403, detail="Invalid current PIN")
    
    # For now, we'll just verify the change is valid
    # In a full implementation, this would update a database record
    # Since we're using config-based PIN, we'll just return success
    # but log the action for audit purposes
    
    if actor_id:
        AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="change_pin",
            entity="system",
            entity_id=str(actor_id),
            meta_data={"operation": "pin_change"}
        )
    
    return {"message": "PIN change requested successfully. Note: PIN is currently managed via configuration."}


@router.get("/{user_id}/balance", response_model=UserBalance)
def get_user_balance(user_id: UUID, db: Session = Depends(get_db)):
    """Get user's current balance"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    balance = BalanceService.get_user_balance(db, str(user_id))
    return UserBalance(user=UserResponse.from_orm(user), balance_cents=balance)


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
