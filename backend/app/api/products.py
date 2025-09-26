from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse)
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
    db_product = Product(**product.dict())
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
    
    return db_product


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
    update_data = product_update.dict(exclude_unset=True)
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