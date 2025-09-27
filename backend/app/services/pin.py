import hashlib
from typing import Optional
from app.core.config import settings


class PinService:
    """Service for handling PIN authentication for treasurer operations"""
    
    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using SHA256"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    @staticmethod
    def verify_pin(pin: str, hashed_pin: Optional[str] = None) -> bool:
        """Verify a PIN against the stored hash"""
        if hashed_pin is None:
            # Compare against the default treasurer PIN from settings
            return PinService.hash_pin(pin) == PinService.hash_pin(settings.treasurer_pin)
        return PinService.hash_pin(pin) == hashed_pin
    
    @staticmethod
    def get_default_pin_hash() -> str:
        """Get the hash of the default treasurer PIN"""
        return PinService.hash_pin(settings.treasurer_pin)