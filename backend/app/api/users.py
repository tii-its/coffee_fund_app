from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models import User, Consumption, MoneyMove, Audit
from app.schemas import (
    UserBalance,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserPinVerificationRequest,
    UserPinChangeRequest,
    AdminUserCreateRequest,
    PinResetRequest,
    PinRecoveryRequest,
)
from app.services.audit import AuditService
from app.services.balance import BalanceService
from app.services.qr_code import QRCodeService
from app.services.pin import PinService
def admin_actor(
    actor_id: UUID = Header(..., alias="x-actor-id"),
    actor_pin: str = Header(..., alias="x-actor-pin"),
    db: Session = Depends(get_db)
):
    """Dependency ensuring the supplied actor is an admin and PIN is valid."""
    user = db.query(User).filter(User.id == actor_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Actor not found")
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Actor is not an admin")
    if not PinService.verify_user_pin(user.id, actor_pin, db):
        raise HTTPException(status_code=403, detail="Invalid admin PIN")
    return user


def treasurer_actor(
    actor_id: UUID = Header(..., alias="x-actor-id"),
    actor_pin: str = Header(..., alias="x-actor-pin"),
    db: Session = Depends(get_db)
):
    """Dependency ensuring the supplied actor is a treasurer and PIN is valid."""
    user = db.query(User).filter(User.id == actor_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Actor not found")
    if user.role not in [UserRole.TREASURER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Actor is not a treasurer or admin")
    if not PinService.verify_user_pin(user.id, actor_pin, db):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    return user
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
    payload: AdminUserCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new user (admin only).

    The request must include an existing admin user's ID and correct PIN.
    Bootstrapping note: If no admin exists yet, allow creation of the first admin without actor credentials.
    """
    admin_user = db.query(User).filter(User.id == payload.actor_id).first()
    target = payload.user

    # Bootstrapping: allow first admin creation if no admin exists in DB
    existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if existing_admin is None and target.role == UserRole.ADMIN:
        # proceed without actor validation
        pass
    else:
        if not admin_user:
            raise HTTPException(status_code=404, detail="Actor (admin) not found")
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Actor is not an admin")
        if not PinService.verify_user_pin(admin_user.id, payload.actor_pin, db):
            raise HTTPException(status_code=403, detail="Invalid admin PIN")

    user_data = target.model_dump(exclude={'pin'})
    user_data['pin_hash'] = PinService.hash_pin(target.pin)
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Audit (only if we had a validated actor)
    if existing_admin is not None:
        AuditService.log_action(
            db=db,
            actor_id=payload.actor_id,
            action="create",
            entity="user",
            entity_id=db_user.id,
            meta_data={"display_name": target.display_name, "role": target.role.value}
        )

    return UserResponse.model_validate(db_user)


@router.get("/", response_model=list[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Get all users (public read access for dashboard and kiosk functionality)"""
    query = db.query(User).filter(User.is_deleted == False)
    if active_only:
        query = query.filter(User.is_active == True)

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db), _admin=Depends(admin_actor)):
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
    admin=Depends(admin_actor)
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

    if admin:
        AuditService.log_action(
            db=db,
            actor_id=admin.id,
            action="update",
            entity="user",
            entity_id=user.id,
            meta_data=update_data
        )

    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    force: bool = Query(False, description="Force delete user even with related records (soft delete)"),
    db: Session = Depends(get_db),
    admin=Depends(admin_actor)
):
    """Delete a user (admin only).

    If user has no related records, performs hard delete (permanent removal).
    If user has related records and force=False, returns 409 with confirmation needed.
    If user has related records and force=True, performs soft delete (sets is_active=False).
    The special admin performing the action cannot delete themselves if they
    are the only remaining admin (safety guard).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting the last remaining admin to avoid lock-out
    if user.role == UserRole.ADMIN:
        remaining_admins = db.query(User).filter(User.role == UserRole.ADMIN, User.id != user.id, User.is_active == True, User.is_deleted == False).count()
        if remaining_admins == 0:
            raise HTTPException(status_code=400, detail="Cannot delete the last remaining admin user")

    # Check for dependent records
    has_consumptions = db.query(Consumption).filter(Consumption.user_id == user.id).first() is not None
    has_created_consumptions = db.query(Consumption).filter(Consumption.created_by == user.id).first() is not None
    has_money_moves = db.query(MoneyMove).filter(MoneyMove.user_id == user.id).first() is not None
    has_created_money_moves = db.query(MoneyMove).filter(MoneyMove.created_by == user.id).first() is not None
    has_confirmed_money_moves = db.query(MoneyMove).filter(MoneyMove.confirmed_by == user.id).first() is not None
    has_audit_entries = db.query(Audit).filter(Audit.actor_id == user.id).first() is not None

    has_related_records = any([
        has_consumptions,
        has_created_consumptions,
        has_money_moves,
        has_created_money_moves,
        has_confirmed_money_moves,
        has_audit_entries,
    ])

    if has_related_records and not force:
        # Return special response indicating confirmation needed
        raise HTTPException(
            status_code=409, 
            detail={
                "error": "user_has_related_records",
                "message": "User has related records. Deletion will deactivate the user permanently but keep their history.",
                "related_records": {
                    "consumptions": has_consumptions,
                    "created_consumptions": has_created_consumptions,
                    "money_moves": has_money_moves,
                    "created_money_moves": has_created_money_moves,
                    "confirmed_money_moves": has_confirmed_money_moves,
                    "audit_entries": has_audit_entries
                },
                "confirmation_required": True
            }
        )

    if has_related_records and force:
        # Soft delete: mark as deleted (but keep active status for clarity)
        user.is_deleted = True
        db.commit()
        db.refresh(user)

        AuditService.log_action(
            db=db,
            actor_id=admin.id,
            action="delete",
            entity="user",
            entity_id=user_id,
            meta_data={"display_name": user.display_name, "soft_delete": True, "forced": True}
        )

        return {"message": "User deleted permanently (soft delete)", "type": "soft_delete"}
    else:
        # Hard delete: no related records
        db.delete(user)
        db.commit()

        AuditService.log_action(
            db=db,
            actor_id=admin.id,
            action="delete",
            entity="user",
            entity_id=user_id,
            meta_data={"display_name": user.display_name, "hard_delete": True}
        )

        return {"message": "User permanently deleted", "type": "hard_delete"}


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


@router.put("/{user_id}/reset-pin")
def reset_user_pin(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(admin_actor)
):
    """Reset user PIN to default '1234' (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not PinService.reset_to_default_pin(user_id, db):
        raise HTTPException(status_code=500, detail="Failed to reset PIN")

    # Log the action
    AuditService.log_action(
        db=db,
        actor_id=admin.id,
        action="reset_pin",
        entity="user",
        entity_id=user_id,
        meta_data={
            "display_name": user.display_name,
            "reset_to_default": True
        }
    )

    return {"message": "PIN reset to default (1234) successfully"}


@router.post("/{user_id}/recover-pin")
def recover_user_pin(
    user_id: UUID,
    recovery_request: PinRecoveryRequest,
    db: Session = Depends(get_db)
):
    """Recover user PIN with verification"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not PinService.recover_user_pin(
        user_id, 
        recovery_request.new_pin,
        recovery_request.verification_method,
        recovery_request.verification_data,
        db
    ):
        if recovery_request.verification_method == 'current_pin':
            raise HTTPException(status_code=403, detail="Invalid current PIN")
        else:
            raise HTTPException(status_code=400, detail="Invalid verification method or data")

    # Log the action (self-recovery)
    AuditService.log_action(
        db=db,
        actor_id=user_id,
        action="recover_pin",
        entity="user",
        entity_id=user_id,
        meta_data={
            "display_name": user.display_name,
            "verification_method": recovery_request.verification_method
        }
    )

    return {"message": "PIN recovered successfully"}
