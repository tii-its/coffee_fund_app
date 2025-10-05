import hashlib
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.users import User


class PinService:
    """Per-user PIN handling service.

    Global admin / treasurer PIN concept removed. Only per-user hashed PINs
    remain.
    """

    @staticmethod
    def hash_pin(pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def verify_user_pin(user_id: UUID, pin: str, db: Session) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.pin_hash:
            return False
        return PinService.hash_pin(pin) == user.pin_hash

    @staticmethod
    def set_user_pin(user_id: UUID, new_pin: str, db: Session) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.pin_hash = PinService.hash_pin(new_pin)
        db.commit()
        return True

    @staticmethod
    def change_user_pin(user_id: UUID, current_pin: str, new_pin: str, db: Session) -> bool:
        if not PinService.verify_user_pin(user_id, current_pin, db):
            return False
        return PinService.set_user_pin(user_id, new_pin, db)
    
    @staticmethod
    def reset_to_default_pin(user_id: UUID, db: Session) -> bool:
        """Reset user PIN to default '1234'"""
        return PinService.set_user_pin(user_id, "1234", db)
    
    @staticmethod
    def recover_user_pin(user_id: UUID, new_pin: str, verification_method: str, verification_data: str, db: Session) -> bool:
        """Recover user PIN with verification"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        # Verify recovery method
        if verification_method == 'current_pin':
            if not PinService.verify_user_pin(user_id, verification_data, db):
                return False
        else:
            # For now, only current PIN verification is supported
            # Email verification could be added in the future
            return False
            
        return PinService.set_user_pin(user_id, new_pin, db)