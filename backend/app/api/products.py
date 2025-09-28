from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.models import Product, Consumption, User
from app.schemas import ProductCreate, ProductUpdate, ProductResponse, ProductConsumptionStats, UserConsumptionStat
from app.services.audit import AuditService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    creator_id: Optional[UUID] = Query(None, description="ID of the user creating this product")
):
    """Create a new product"""
    # Check if product with this name already exists
    existing_product = db.query(Product).filter(Product.name == product.name).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this name already exists")
    
    # Create new product
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Log action
    if creator_id:
        AuditService.log_action(
            db=db,
            actor_id=creator_id,
            action="create",
            entity="product",
            entity_id=db_product.id,
            meta_data={"name": product.name, "price_cents": product.price_cents}
        )
    
    return ProductResponse.model_validate(db_product)


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all products"""
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/top-consumers", response_model=List[ProductConsumptionStats])
def get_products_with_top_consumers(
    limit_per_product: int = Query(3, description="Number of top consumers per product"),
    db: Session = Depends(get_db)
):
    """Get all products with their top consumers"""
    # Get all active products
    products = db.query(Product).filter(Product.is_active == True).all()
    
    result = []
    for product in products:
        # Get top consumers for this product
        top_consumers_query = (
            db.query(
                Consumption.user_id,
                User.display_name,
                func.sum(Consumption.qty).label('total_qty'),
                func.sum(Consumption.amount_cents).label('total_amount_cents')
            )
            .join(User, Consumption.user_id == User.id)
            .filter(Consumption.product_id == product.id)
            .group_by(Consumption.user_id, User.display_name)
            .order_by(desc(func.sum(Consumption.qty)))
            .limit(limit_per_product)
            .all()
        )
        
        # Convert to response format
        top_consumers = [
            UserConsumptionStat(
                user_id=consumer.user_id,
                display_name=consumer.display_name,
                total_qty=consumer.total_qty,
                total_amount_cents=consumer.total_amount_cents
            )
            for consumer in top_consumers_query
        ]
        
        # Only include products that have consumptions
        if top_consumers:
            result.append(ProductConsumptionStats(
                product=ProductResponse.model_validate(product),
                top_consumers=top_consumers
            ))
    
    return result


@router.get("/latest", response_model=Optional[ProductResponse])
def get_latest_product(db: Session = Depends(get_db)):
    """Get the latest added product"""
    product = (
        db.query(Product)
        .filter(Product.is_active == True)
        .order_by(Product.created_at.desc())
        .first()
    )
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get a specific product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    actor_id: Optional[UUID] = Query(None, description="ID of the user performing the update")
):
    """Update a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Log action
    if actor_id:
        AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="update",
            entity="product",
            entity_id=product.id,
            meta_data=update_data
        )
    
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    actor_id: Optional[UUID] = Query(None, description="ID of the user performing the delete")
):
    """Deactivate a product (soft delete)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    
    # Log action
    if actor_id:
        AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="delete",
            entity="product",
            entity_id=product.id,
            meta_data={"name": product.name}
        )
    
    return {"message": "Product deactivated successfully"}