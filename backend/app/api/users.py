from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.models import User
from app.schemas import UserCreate, UserUpdate, UserResponse, UserBalance
from app.services.balance import BalanceService
from app.services.audit import AuditService
from app.services.qr_code import QRCodeService
from app.core.enums import UserRole

router = APIRouter(prefix="/users", tags=["users"])


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


@router.get("/", response_model=List[UserResponse])
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
    """Update a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
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


@router.get("/balances/all", response_model=List[UserBalance])
def get_all_balances(db: Session = Depends(get_db)):
    """Get balances for all users"""
    return BalanceService.get_all_user_balances(db)


@router.get("/balances/below-threshold", response_model=List[UserBalance])
def get_users_below_threshold(
    threshold_cents: int = Query(1000, description="Threshold in cents"),
    db: Session = Depends(get_db)
):
    """Get users with balance below threshold"""
    return BalanceService.get_users_below_threshold(db, threshold_cents)


@router.get("/balances/above-threshold", response_model=List[UserBalance])
def get_users_above_threshold(
    threshold_cents: int = Query(1000, description="Threshold in cents"),
    db: Session = Depends(get_db)
):
    """Get users with balance above or equal to threshold"""
    return BalanceService.get_users_above_threshold(db, threshold_cents)