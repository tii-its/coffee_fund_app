from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models import StockPurchase, User
from app.schemas import (
    StockPurchaseCreate, 
    StockPurchaseUpdate, 
    StockPurchaseResponse, 
    StockPurchaseWithCreator
)
from app.services.audit import AuditService
from app.core.enums import UserRole

router = APIRouter(prefix="/stock-purchases", tags=["stock-purchases"])


@router.post("/", response_model=StockPurchaseResponse, status_code=201)
def create_stock_purchase(
    stock_purchase: StockPurchaseCreate,
    creator_id: UUID = Query(..., description="ID of the user creating this stock purchase"),
    db: Session = Depends(get_db)
):
    """Create a new stock purchase record"""
    # Verify creator exists and has treasurer role
    creator = db.query(User).filter(User.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    if creator.role != UserRole.TREASURER:
        raise HTTPException(status_code=403, detail="Only treasurers can create stock purchases")
    
    # Create stock purchase
    db_stock_purchase = StockPurchase(
        **stock_purchase.model_dump(),
        created_by=creator_id
    )
    
    db.add(db_stock_purchase)
    db.commit()
    db.refresh(db_stock_purchase)
    
    # Log action
    AuditService.log_action(
        db=db,
        actor_id=creator_id,
        action="stock_purchase_created",
        entity="stock_purchase",
        entity_id=db_stock_purchase.id,
        meta_json={
            "item_name": stock_purchase.item_name,
            "quantity": stock_purchase.quantity,
            "total_amount_cents": stock_purchase.total_amount_cents,
            "supplier": stock_purchase.supplier,
        }
    )
    
    return StockPurchaseResponse.model_validate(db_stock_purchase)


@router.get("/", response_model=List[StockPurchaseWithCreator])
def get_stock_purchases(
    skip: int = 0,
    limit: int = 100,
    cash_out_processed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get stock purchases with optional filtering"""
    query = db.query(StockPurchase)
    
    if cash_out_processed is not None:
        query = query.filter(StockPurchase.is_cash_out_processed == cash_out_processed)
    
    stock_purchases = (
        query.order_by(desc(StockPurchase.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert to response format with creator info
    result = []
    for sp in stock_purchases:
        sp_dict = StockPurchaseResponse.model_validate(sp).model_dump()
        sp_dict['creator'] = {
            'id': str(sp.creator.id),
            'display_name': sp.creator.display_name,
            'role': sp.creator.role.value
        }
        result.append(sp_dict)
    
    return result


@router.get("/{stock_purchase_id}", response_model=StockPurchaseWithCreator)
def get_stock_purchase(stock_purchase_id: UUID, db: Session = Depends(get_db)):
    """Get a specific stock purchase"""
    stock_purchase = db.query(StockPurchase).filter(StockPurchase.id == stock_purchase_id).first()
    if not stock_purchase:
        raise HTTPException(status_code=404, detail="Stock purchase not found")
    
    sp_dict = StockPurchaseResponse.model_validate(stock_purchase).model_dump()
    sp_dict['creator'] = {
        'id': str(stock_purchase.creator.id),
        'display_name': stock_purchase.creator.display_name,
        'role': stock_purchase.creator.role.value
    }
    
    return sp_dict


@router.patch("/{stock_purchase_id}", response_model=StockPurchaseResponse)
def update_stock_purchase(
    stock_purchase_id: UUID,
    stock_purchase_update: StockPurchaseUpdate,
    actor_id: UUID = Query(..., description="ID of the user updating this stock purchase"),
    db: Session = Depends(get_db)
):
    """Update a stock purchase"""
    # Verify actor exists and has treasurer role
    actor = db.query(User).filter(User.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    if actor.role != UserRole.TREASURER:
        raise HTTPException(status_code=403, detail="Only treasurers can update stock purchases")
    
    # Get stock purchase
    stock_purchase = db.query(StockPurchase).filter(StockPurchase.id == stock_purchase_id).first()
    if not stock_purchase:
        raise HTTPException(status_code=404, detail="Stock purchase not found")
    
    # Update fields
    update_data = stock_purchase_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stock_purchase, field, value)
    
    db.commit()
    db.refresh(stock_purchase)
    
    # Log action
    AuditService.log_action(
        db=db,
        actor_id=actor_id,
        action="stock_purchase_updated",
        entity="stock_purchase",
        entity_id=stock_purchase.id,
        meta_json=update_data
    )
    
    return StockPurchaseResponse.model_validate(stock_purchase)


@router.patch("/{stock_purchase_id}/cash-out", response_model=StockPurchaseResponse)
def process_cash_out(
    stock_purchase_id: UUID,
    actor_id: UUID = Query(..., description="ID of the user processing the cash out"),
    db: Session = Depends(get_db)
):
    """Mark a stock purchase as cash out processed"""
    # Verify actor exists and has treasurer role
    actor = db.query(User).filter(User.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    if actor.role != UserRole.TREASURER:
        raise HTTPException(status_code=403, detail="Only treasurers can process cash out")
    
    # Get stock purchase
    stock_purchase = db.query(StockPurchase).filter(StockPurchase.id == stock_purchase_id).first()
    if not stock_purchase:
        raise HTTPException(status_code=404, detail="Stock purchase not found")
    
    if stock_purchase.is_cash_out_processed:
        raise HTTPException(status_code=400, detail="Cash out already processed")
    
    # Mark as processed
    stock_purchase.is_cash_out_processed = True
    
    db.commit()
    db.refresh(stock_purchase)
    
    # Log action
    AuditService.log_action(
        db=db,
        actor_id=actor_id,
        action="stock_purchase_cash_out_processed",
        entity="stock_purchase",
        entity_id=stock_purchase.id,
        meta_json={
            "total_amount_cents": stock_purchase.total_amount_cents,
            "item_name": stock_purchase.item_name
        }
    )
    
    return StockPurchaseResponse.model_validate(stock_purchase)


@router.delete("/{stock_purchase_id}")
def delete_stock_purchase(
    stock_purchase_id: UUID,
    actor_id: UUID = Query(..., description="ID of the user deleting this stock purchase"),
    db: Session = Depends(get_db)
):
    """Delete a stock purchase"""
    # Verify actor exists and has treasurer role
    actor = db.query(User).filter(User.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    if actor.role != UserRole.TREASURER:
        raise HTTPException(status_code=403, detail="Only treasurers can delete stock purchases")
    
    # Get stock purchase
    stock_purchase = db.query(StockPurchase).filter(StockPurchase.id == stock_purchase_id).first()
    if not stock_purchase:
        raise HTTPException(status_code=404, detail="Stock purchase not found")
    
    # Log action before deletion
    AuditService.log_action(
        db=db,
        actor_id=actor_id,
        action="stock_purchase_deleted",
        entity="stock_purchase",
        entity_id=stock_purchase.id,
        meta_json={
            "item_name": stock_purchase.item_name,
            "total_amount_cents": stock_purchase.total_amount_cents
        }
    )
    
    db.delete(stock_purchase)
    db.commit()
    
    return {"message": "Stock purchase deleted successfully"}