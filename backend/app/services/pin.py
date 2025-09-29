import hashlib
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.system_settings import SystemSettings
from app.models.users import User
from datetime import datetime


class PinService:
    """Service for handling global admin PIN (formerly treasurer PIN).

    Backward compatibility:
      - Database key renamed from 'treasurer_pin_hash' to 'admin_pin_hash'.
      - Env var TREASURER_PIN deprecated; ADMIN_PIN preferred.
    This service looks for the new key first, then falls back to the legacy key.
    """

    ADMIN_PIN_KEY = "admin_pin_hash"
    TREASURER_PIN_KEY = "treasurer_pin_hash"  # legacy constant (do not remove until deprecation window passes)
    # TODO: Remove TREASURER_PIN_KEY fallback and positional (pin, hash) ambiguity support after deprecation window (set target release date)

    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using SHA256"""
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def get_current_pin_hash(db: Session) -> str:
        """Get the current admin PIN hash from database or fallback.

        Order of resolution:
          1. admin_pin_hash (new)
          2. treasurer_pin_hash (legacy) – silent usage (could log later)
          3. settings.admin_pin value (hashed)
        """
        # New key first
        setting = db.query(SystemSettings).filter(SystemSettings.key == PinService.ADMIN_PIN_KEY).first()
        if setting and setting.value:
            return setting.value

        # Legacy key fallback
        legacy = db.query(SystemSettings).filter(SystemSettings.key == PinService.TREASURER_PIN_KEY).first()
        if legacy and legacy.value:
            return legacy.value

        # Fallback to config (hash on the fly)
        return PinService.hash_pin(settings.admin_pin)

    @staticmethod
    def verify_treasurer_pin(pin: str, db: Optional[Session] = None, hashed_pin: Optional[str] = None) -> bool:
        """Verify a PIN against the stored treasurer hash.

        Backwards compatibility: some tests may call verify_pin(pin, hashed_pin)
        thinking the second positional arg is the hash. Detect this pattern by
        checking if 'db' is a string of plausible hash length (64 hex chars for SHA256).
        """
        # If caller passed (pin, hashed_pin) positionally
        if db is not None and hashed_pin is None and isinstance(db, str) and len(db) == 64:
            hashed_pin = db  # reinterpret second positional argument as hash
            db = None

        if hashed_pin is not None:
            return PinService.hash_pin(pin) == hashed_pin

        if db is not None:
            current_hash = PinService.get_current_pin_hash(db)
            return PinService.hash_pin(pin) == current_hash

        # Fallback to settings-based verification (default admin PIN)
        return PinService.hash_pin(pin) == PinService.hash_pin(settings.admin_pin)

    @staticmethod
    def verify_pin(pin: str, db: Optional[Session] = None, hashed_pin: Optional[str] = None) -> bool:
        """Legacy method for backwards compatibility - delegates to verify_treasurer_pin"""
        return PinService.verify_treasurer_pin(pin, db, hashed_pin)
    
    @staticmethod
    def verify_user_pin(user_id: UUID, pin: str, db: Session) -> bool:
        """Verify a user's PIN against their stored hash"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.pin_hash:
            return False
        
        return PinService.hash_pin(pin) == user.pin_hash
    
    @staticmethod
    def set_user_pin(user_id: UUID, new_pin: str, db: Session) -> bool:
        """Set a user's PIN"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.pin_hash = PinService.hash_pin(new_pin)
        db.commit()
        return True
    
    @staticmethod
    def change_user_pin(user_id: UUID, current_pin: str, new_pin: str, db: Session) -> bool:
        """Change a user's PIN after verifying the current PIN"""
        # Verify current PIN first
        if not PinService.verify_user_pin(user_id, current_pin, db):
            return False
        
        # Set new PIN
        return PinService.set_user_pin(user_id, new_pin, db)
    
    @staticmethod
    def change_pin(db: Session, current_pin: str, new_pin: str) -> bool:
        """Change the admin PIN after verifying the current PIN (migrates legacy key)."""
        # Verify current PIN first
        if not PinService.verify_treasurer_pin(current_pin, db=db):
            return False

        # Hash the new PIN
        new_pin_hash = PinService.hash_pin(new_pin)

        # Prefer new key; if only legacy exists, migrate in-place.
        setting = db.query(SystemSettings).filter(SystemSettings.key == PinService.ADMIN_PIN_KEY).first()
        if not setting:
            legacy = db.query(SystemSettings).filter(SystemSettings.key == PinService.TREASURER_PIN_KEY).first()
            if legacy:
                legacy.key = PinService.ADMIN_PIN_KEY
                setting = legacy

        if setting:
            setting.value = new_pin_hash
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSettings(
                key=PinService.ADMIN_PIN_KEY,
                value=new_pin_hash,
                is_encrypted=False
            )
            db.add(setting)

        db.commit()
        return True

    @staticmethod
    def get_default_pin_hash() -> str:
        """Get the hash of the default admin PIN"""
        return PinService.hash_pin(settings.admin_pin)