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