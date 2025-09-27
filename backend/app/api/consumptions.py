from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_db
from app.models import Consumption, User, Product
from app.schemas import ConsumptionCreate, ConsumptionResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/consumptions", tags=["consumptions"])


@router.post("/", response_model=ConsumptionResponse, status_code=201)
def create_consumption(
    consumption: ConsumptionCreate,
    creator_id: UUID = Query(..., description="ID of the user creating this consumption"),
    db: Session = Depends(get_db)
):
    """Create a new consumption"""
    # Verify user exists
    user = db.query(User).filter(User.id == consumption.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify product exists and is active
    product = db.query(Product).filter(
        Product.id == consumption.product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    
    # Calculate amounts
    unit_price_cents = product.price_cents
    amount_cents = unit_price_cents * consumption.qty
    
    # Create consumption
    db_consumption = Consumption(
        user_id=consumption.user_id,
        product_id=consumption.product_id,
        qty=consumption.qty,
        unit_price_cents=unit_price_cents,
        amount_cents=amount_cents,
        created_by=creator_id
    )
    
    db.add(db_consumption)
    db.commit()
    db.refresh(db_consumption)
    
    # Log action
    AuditService.log_consumption_created(
        db=db,
        actor_id=creator_id,
        consumption_id=db_consumption.id,
        user_id=consumption.user_id,
        product_name=product.name,
        qty=consumption.qty,
        amount_cents=amount_cents
    )
    
    return ConsumptionResponse.model_validate(db_consumption)


@router.get("/", response_model=List[ConsumptionResponse])
def get_consumptions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get consumptions with optional filtering"""
    query = db.query(Consumption)
    
    if user_id:
        query = query.filter(Consumption.user_id == user_id)
    if product_id:
        query = query.filter(Consumption.product_id == product_id)
    
    consumptions = (
        query.order_by(Consumption.at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return consumptions


@router.get("/{consumption_id}", response_model=ConsumptionResponse)
def get_consumption(consumption_id: UUID, db: Session = Depends(get_db)):
    """Get a specific consumption"""
    consumption = db.query(Consumption).filter(Consumption.id == consumption_id).first()
    if not consumption:
        raise HTTPException(status_code=404, detail="Consumption not found")
    return consumption


@router.get("/user/{user_id}/recent", response_model=List[ConsumptionResponse])
def get_user_recent_consumptions(
    user_id: UUID,
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """Get recent consumptions for a specific user"""
    consumptions = (
        db.query(Consumption)
        .filter(Consumption.user_id == user_id)
        .order_by(Consumption.at.desc())
        .limit(limit)
        .all()
    )
    return consumptions