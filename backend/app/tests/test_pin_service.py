import pytest
import hashlib
from app.services.pin import PinService
from app.core.config import settings


class TestPinService:
    """Test the PIN service functionality"""

    def test_hash_pin(self):
        """Test PIN hashing"""
        pin = "1234"
        expected_hash = hashlib.sha256(pin.encode()).hexdigest()
        assert PinService.hash_pin(pin) == expected_hash

    def test_verify_pin_with_default(self):
        """Test PIN verification against default treasurer PIN"""
        # Should verify against the default treasurer PIN from settings
        assert PinService.verify_pin(settings.treasurer_pin) is True
        assert PinService.verify_pin("wrong-pin") is False

    def test_verify_pin_with_provided_hash(self):
        """Test PIN verification with provided hash"""
        pin = "test123"
        hashed_pin = PinService.hash_pin(pin)
        
        assert PinService.verify_pin(pin, hashed_pin) is True
        assert PinService.verify_pin("wrong", hashed_pin) is False

    def test_get_default_pin_hash(self):
        """Test getting default PIN hash"""
        expected = PinService.hash_pin(settings.treasurer_pin)
        assert PinService.get_default_pin_hash() == expected