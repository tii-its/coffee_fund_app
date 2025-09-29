import pytest
import hashlib
from uuid import uuid4
from app.services.pin import PinService
from app.core.config import settings
from app.models.users import User
from app.core.enums import UserRole


class TestPinService:
    """Test the PIN service functionality"""

    def test_hash_pin(self):
        """Test PIN hashing"""
        pin = "1234"
        expected_hash = hashlib.sha256(pin.encode()).hexdigest()
        assert PinService.hash_pin(pin) == expected_hash

    def test_verify_treasurer_pin_with_default(self):
        """Test treasurer PIN verification against default PIN"""
        # Should verify against the default treasurer PIN from settings
        assert PinService.verify_treasurer_pin(settings.treasurer_pin) is True
        assert PinService.verify_treasurer_pin("wrong-pin") is False

    def test_verify_pin_backwards_compatibility(self):
        """Test backwards compatibility for verify_pin method"""
        # Should still work for treasurer PIN verification
        assert PinService.verify_pin(settings.treasurer_pin) is True
        assert PinService.verify_pin("wrong-pin") is False

    def test_verify_pin_with_provided_hash(self):
        """Test PIN verification with provided hash"""
        pin = "test123"
        hashed_pin = PinService.hash_pin(pin)
        
        assert PinService.verify_treasurer_pin(pin, hashed_pin) is True
        assert PinService.verify_treasurer_pin("wrong", hashed_pin) is False

    def test_verify_user_pin(self, db_session):
        """Test user PIN verification"""
        # Create a test user with PIN
        user = User(
            display_name="Test User",
            email="test@example.com",
            role=UserRole.USER,
            pin_hash=PinService.hash_pin("user123")
        )
        db_session.add(user)
        db_session.commit()
        
        # Test PIN verification
        assert PinService.verify_user_pin(user.id, "user123", db_session) is True
        assert PinService.verify_user_pin(user.id, "wrong-pin", db_session) is False
        
        # Test with non-existent user
        fake_user_id = uuid4()
        assert PinService.verify_user_pin(fake_user_id, "any-pin", db_session) is False

    def test_set_user_pin(self, db_session):
        """Test setting user PIN"""
        # Create a test user without PIN
        user = User(
            display_name="Test User",
            email="test2@example.com",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()
        
        # Set PIN
        assert PinService.set_user_pin(user.id, "new-pin-456", db_session) is True
        
        # Verify PIN was set
        db_session.refresh(user)
        assert user.pin_hash == PinService.hash_pin("new-pin-456")
        
        # Test with non-existent user
        fake_user_id = uuid4()
        assert PinService.set_user_pin(fake_user_id, "any-pin", db_session) is False

    def test_change_user_pin(self, db_session):
        """Test changing user PIN"""
        # Create a test user with PIN
        user = User(
            display_name="Test User",
            email="test3@example.com",
            role=UserRole.USER,
            pin_hash=PinService.hash_pin("old-pin")
        )
        db_session.add(user)
        db_session.commit()
        
        # Change PIN with correct old PIN
        assert PinService.change_user_pin(user.id, "old-pin", "new-pin", db_session) is True
        
        # Verify old PIN no longer works
        assert PinService.verify_user_pin(user.id, "old-pin", db_session) is False
        # Verify new PIN works
        assert PinService.verify_user_pin(user.id, "new-pin", db_session) is True
        
        # Try to change PIN with wrong old PIN
        assert PinService.change_user_pin(user.id, "wrong-old-pin", "another-new-pin", db_session) is False

    def test_get_default_pin_hash(self):
        """Test getting default PIN hash"""
        expected = PinService.hash_pin(settings.treasurer_pin)
        assert PinService.get_default_pin_hash() == expected