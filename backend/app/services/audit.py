from sqlalchemy.orm import Session
from app.models import Audit, User
from app.core.enums import AuditAction
from typing import Dict, Any, Optional
from uuid import UUID
import json


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        actor_id: UUID,
        action: str,
        entity: str,
        entity_id: UUID,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Audit:
        """Log an audit entry"""
        audit_entry = Audit(
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            meta_json=meta_data
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def log_consumption_created(
        db: Session,
        actor_id: UUID,
        consumption_id: UUID,
        user_id: UUID,
        product_name: str,
        qty: int,
        amount_cents: int
    ):
        """Log consumption creation"""
        return AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.CREATE,
            entity="consumption",
            entity_id=consumption_id,
            meta_data={
                "user_id": str(user_id),
                "product_name": product_name,
                "qty": qty,
                "amount_cents": amount_cents
            }
        )

    @staticmethod
    def log_money_move_created(
        db: Session,
        actor_id: UUID,
        money_move_id: UUID,
        move_type: str,
        user_id: UUID,
        amount_cents: int,
        note: Optional[str] = None
    ):
        """Log money move creation"""
        return AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action=AuditAction.CREATE,
            entity="money_move",
            entity_id=money_move_id,
            meta_data={
                "type": move_type,
                "user_id": str(user_id),
                "amount_cents": amount_cents,
                "note": note
            }
        )

    @staticmethod
    def log_money_move_confirmed(
        db: Session,
        actor_id: UUID,
        money_move_id: UUID,
        status: str
    ):
        """Log money move confirmation/rejection"""
        action = AuditAction.CONFIRM if status == "confirmed" else AuditAction.REJECT
        return AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action=action,
            entity="money_move",
            entity_id=money_move_id,
            meta_data={"status": status}
        )