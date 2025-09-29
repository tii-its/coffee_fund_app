from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, UTC
from app.db.session import get_db
from app.models import MoneyMove, User
from app.schemas import MoneyMoveCreate, MoneyMoveUpdate, MoneyMoveResponse
from app.services.audit import AuditService
from app.core.enums import MoneyMoveStatus, UserRole

router = APIRouter(prefix="/money-moves", tags=["money-moves"])


@router.post("/", response_model=MoneyMoveResponse, status_code=201)
def create_money_move(
    money_move: MoneyMoveCreate,
    creator_id: UUID = Query(..., description="ID of the user creating this money move"),
    db: Session = Depends(get_db)
):
    """Create a new money move (requires two-person confirmation)"""
    # Verify target user exists
    user = db.query(User).filter(User.id == money_move.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify creator exists and has treasurer role
    creator = db.query(User).filter(User.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    if creator.role != UserRole.TREASURER:
        raise HTTPException(status_code=403, detail="Only treasurers can create money moves")
    
    # Create money move in pending status
    db_money_move = MoneyMove(
        type=money_move.type,
        user_id=money_move.user_id,
        amount_cents=money_move.amount_cents,
        note=money_move.note,
        created_by=creator_id,
        status=MoneyMoveStatus.PENDING
    )
    
    db.add(db_money_move)
    db.commit()
    db.refresh(db_money_move)
    
    # Log action
    AuditService.log_money_move_created(
        db=db,
        actor_id=creator_id,
        money_move_id=db_money_move.id,
        move_type=money_move.type.value,
        user_id=money_move.user_id,
        amount_cents=money_move.amount_cents,
        note=money_move.note
    )
    
    return MoneyMoveResponse.model_validate(db_money_move)


@router.get("/", response_model=List[MoneyMoveResponse])
def get_money_moves(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
    status: Optional[MoneyMoveStatus] = None,
    db: Session = Depends(get_db)
):
    """Get money moves with optional filtering"""
    query = db.query(MoneyMove)
    
    if user_id:
        query = query.filter(MoneyMove.user_id == user_id)
    if status:
        query = query.filter(MoneyMove.status == status)
    
    money_moves = (
        query.order_by(MoneyMove.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return money_moves


@router.get("/pending", response_model=List[MoneyMoveResponse])
def get_pending_money_moves(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all pending money moves"""
    money_moves = (
        db.query(MoneyMove)
        .filter(MoneyMove.status == MoneyMoveStatus.PENDING)
        .order_by(MoneyMove.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return money_moves


@router.get("/{money_move_id}", response_model=MoneyMoveResponse)
def get_money_move(money_move_id: UUID, db: Session = Depends(get_db)):
    """Get a specific money move"""
    money_move = db.query(MoneyMove).filter(MoneyMove.id == money_move_id).first()
    if not money_move:
        raise HTTPException(status_code=404, detail="Money move not found")
    return money_move


@router.patch("/{money_move_id}/confirm", response_model=MoneyMoveResponse)
def confirm_money_move(
    money_move_id: UUID,
    confirmer_id: UUID = Query(..., description="ID of the user confirming this money move"),
    db: Session = Depends(get_db)
):
    """Confirm a pending money move"""
    # Get money move
    money_move = db.query(MoneyMove).filter(MoneyMove.id == money_move_id).first()
    if not money_move:
        raise HTTPException(status_code=404, detail="Money move not found")
    
    if money_move.status != MoneyMoveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Money move is not pending")
    
    # Verify confirmer exists
    confirmer = db.query(User).filter(User.id == confirmer_id).first()
    if not confirmer:
        raise HTTPException(status_code=404, detail="Confirmer not found")
    
    # Prevent self-confirmation
    if money_move.created_by == confirmer_id:
        raise HTTPException(status_code=400, detail="Cannot confirm own money move")
    
    # Update money move
    money_move.status = MoneyMoveStatus.CONFIRMED
    money_move.confirmed_at = datetime.now(UTC)
    money_move.confirmed_by = confirmer_id
    
    db.commit()
    db.refresh(money_move)
    
    # Log action
    AuditService.log_money_move_confirmed(
        db=db,
        actor_id=confirmer_id,
        money_move_id=money_move.id,
        status="confirmed"
    )
    
    return money_move


@router.patch("/{money_move_id}/reject", response_model=MoneyMoveResponse)
def reject_money_move(
    money_move_id: UUID,
    rejector_id: UUID = Query(..., description="ID of the user rejecting this money move"),
    db: Session = Depends(get_db)
):
    """Reject a pending money move"""
    # Get money move
    money_move = db.query(MoneyMove).filter(MoneyMove.id == money_move_id).first()
    if not money_move:
        raise HTTPException(status_code=404, detail="Money move not found")
    
    if money_move.status != MoneyMoveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Money move is not pending")
    
    # Verify rejector exists
    rejector = db.query(User).filter(User.id == rejector_id).first()
    if not rejector:
        raise HTTPException(status_code=404, detail="Rejector not found")
    
    # Update money move
    money_move.status = MoneyMoveStatus.REJECTED
    money_move.confirmed_at = datetime.now(UTC)
    money_move.confirmed_by = rejector_id
    
    db.commit()
    db.refresh(money_move)
    
    # Log action
    AuditService.log_money_move_confirmed(
        db=db,
        actor_id=rejector_id,
        money_move_id=money_move.id,
        status="rejected"
    )
    
    return money_move