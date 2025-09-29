import hashlib
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.users import User
from app.services.audit import AuditService


class UserPinService:
    """Service for handling individual user PINs."""

    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using SHA256"""
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def verify_user_pin(db: Session, user_id: UUID, pin: str) -> bool:
        """Verify a user's PIN."""
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user or not user.pin_hash:
            return False
        return UserPinService.hash_pin(pin) == user.pin_hash

    @staticmethod
    def change_user_pin(db: Session, user_id: UUID, current_pin: str, new_pin: str, actor_id: Optional[UUID] = None) -> bool:
        """Change a user's PIN after verifying the current PIN."""
        # Verify current PIN first
        if not UserPinService.verify_user_pin(db, user_id, current_pin):
            return False

        # Get user and update PIN
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return False

        user.pin_hash = UserPinService.hash_pin(new_pin)
        db.commit()

        # Log the action for audit purposes
        if actor_id:
            AuditService.log_action(
                db=db,
                actor_id=actor_id,
                action="change_user_pin",
                entity="user",
                entity_id=user_id,
                meta_data={"target_user": str(user_id)}
            )

        return True

    @staticmethod
    def set_user_pin(db: Session, user_id: UUID, new_pin: str, actor_id: Optional[UUID] = None) -> bool:
        """Set a user's PIN (admin operation, doesn't require current PIN)."""
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return False

        user.pin_hash = UserPinService.hash_pin(new_pin)
        db.commit()

        # Log the action for audit purposes
        if actor_id:
            AuditService.log_action(
                db=db,
                actor_id=actor_id,
                action="set_user_pin",
                entity="user",
                entity_id=user_id,
                meta_data={"target_user": str(user_id)}
            )

        return True