import pytest
import hashlib
from uuid import uuid4
from app.services.pin import PinService
from app.models.users import User
from app.core.enums import UserRole


class TestPinService:
    """Test the PIN service functionality"""

    def test_hash_pin(self):
        """Test PIN hashing"""
        pin = "1234"
        expected_hash = hashlib.sha256(pin.encode()).hexdigest()
        assert PinService.hash_pin(pin) == expected_hash

    # Removed global/default pin verification tests (legacy feature deleted)

    def test_verify_user_pin(self, db_session):
        """Test user PIN verification"""
        # Create a test user with PIN
        user = User(
            display_name="Test User",
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

    # Removed default hash retrieval test (no global PIN concept)