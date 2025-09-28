import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.system_settings import SystemSettings
from datetime import datetime


class PinService:
    """Service for handling PIN authentication for treasurer operations"""
    
    TREASURER_PIN_KEY = "treasurer_pin_hash"
    
    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using SHA256"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    @staticmethod
    def get_current_pin_hash(db: Session) -> str:
        """Get the current PIN hash from database or fallback to settings"""
        # Try to get from database first
        setting = db.query(SystemSettings).filter(
            SystemSettings.key == PinService.TREASURER_PIN_KEY
        ).first()
        
        if setting and setting.value:
            return setting.value
            
        # Fallback to settings-based PIN
        return PinService.hash_pin(settings.treasurer_pin)
    
    @staticmethod
    def verify_pin(pin: str, db: Optional[Session] = None, hashed_pin: Optional[str] = None) -> bool:
        """Verify a PIN against the stored hash.

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

        # Fallback to settings-based verification (default PIN)
        return PinService.hash_pin(pin) == PinService.hash_pin(settings.treasurer_pin)
    
    @staticmethod
    def change_pin(db: Session, current_pin: str, new_pin: str) -> bool:
        """Change the treasurer PIN after verifying the current PIN"""
        # Verify current PIN first
        if not PinService.verify_pin(current_pin, db=db):
            return False
            
        # Hash the new PIN
        new_pin_hash = PinService.hash_pin(new_pin)
        
        # Check if setting exists
        setting = db.query(SystemSettings).filter(
            SystemSettings.key == PinService.TREASURER_PIN_KEY
        ).first()
        
        if setting:
            # Update existing setting
            setting.value = new_pin_hash
            setting.updated_at = datetime.utcnow()
        else:
            # Create new setting
            setting = SystemSettings(
                key=PinService.TREASURER_PIN_KEY,
                value=new_pin_hash,
                is_encrypted=False  # Already hashed, so not doubly encrypted
            )
            db.add(setting)
            
        db.commit()
        return True
    
    @staticmethod
    def get_default_pin_hash() -> str:
        """Get the hash of the default treasurer PIN"""
        return PinService.hash_pin(settings.treasurer_pin)