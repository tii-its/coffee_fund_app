from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.models import Audit
from app.schemas import AuditResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[AuditResponse])
def get_audit_entries(
    skip: int = 0,
    limit: int = 100,
    actor_id: Optional[UUID] = None,
    entity: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get audit entries with optional filtering"""
    query = db.query(Audit)
    
    if actor_id:
        query = query.filter(Audit.actor_id == actor_id)
    if entity:
        query = query.filter(Audit.entity == entity)
    if entity_id:
        query = query.filter(Audit.entity_id == entity_id)
    
    audit_entries = (
        query.order_by(Audit.at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return audit_entries


@router.get("/{audit_id}", response_model=AuditResponse)
def get_audit_entry(audit_id: UUID, db: Session = Depends(get_db)):
    """Get a specific audit entry"""
    audit_entry = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit_entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return audit_entry