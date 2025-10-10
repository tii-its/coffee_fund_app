from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_db
from app.models import Consumption, User, Product
from app.services.pin import PinService
from app.core.enums import UserRole
from app.schemas import ConsumptionCreate, ConsumptionResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/consumptions", tags=["consumptions"])


def user_or_treasurer_actor(
    actor_id: UUID = Header(..., alias="x-actor-id"),
    actor_pin: str = Header(..., alias="x-actor-pin"),
    db: Session = Depends(get_db)
):
    """Allow either a treasurer or the user themselves (with correct PIN)."""
    actor = db.query(User).filter(User.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    if not actor.is_active:
        raise HTTPException(status_code=403, detail="Actor inactive")
    if not PinService.verify_user_pin(actor.id, actor_pin, db):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    return actor


@router.post("/", response_model=ConsumptionResponse, status_code=201)
def create_consumption(
    consumption: ConsumptionCreate,
    db: Session = Depends(get_db),
    actor=Depends(user_or_treasurer_actor)
):
    """Create a new consumption.

    Allowed:
      * Treasurer (can book for any user)
      * The user themself (user_id == actor.id)
    """
    # Verify user exists
    user = db.query(User).filter(User.id == consumption.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Authorization: if actor is not treasurer, must be same user
    if actor.role != UserRole.TREASURER and actor.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to book for this user")
    
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
    # Explicitly set timestamp in Python to gain higher resolution than some
    # SQLite func.now() implementations (improves deterministic ordering in tests)
    from datetime import datetime, timezone
    db_consumption = Consumption(
        user_id=consumption.user_id,
        product_id=consumption.product_id,
        qty=consumption.qty,
        unit_price_cents=unit_price_cents,
        amount_cents=amount_cents,
        created_by=actor.id,
        at=datetime.now(timezone.utc)
    )
    
    db.add(db_consumption)
    db.commit()
    db.refresh(db_consumption)
    
    # Log action
    AuditService.log_consumption_created(
        db=db,
        actor_id=actor.id,
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
        # Order by timestamp desc, then by id desc to break same-timestamp ties
        .order_by(Consumption.at.desc(), Consumption.id.desc())
        .limit(limit)
        .all()
    )
    return consumptions