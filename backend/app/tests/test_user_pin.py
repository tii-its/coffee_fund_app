import pytest
from uuid import uuid4
from app.services.user_pin import UserPinService
from app.models.users import User
from app.core.enums import UserRole


class TestUserPinService:
    """Test the User PIN service functionality"""

    def test_hash_pin(self):
        """Test PIN hashing"""
        pin = "1234"
        hash1 = UserPinService.hash_pin(pin)
        hash2 = UserPinService.hash_pin(pin)
        
        # Same PIN should produce same hash
        assert hash1 == hash2
        
        # Different PINs should produce different hashes
        different_hash = UserPinService.hash_pin("5678")
        assert hash1 != different_hash

    def test_verify_user_pin_success(self, db_session):
        """Test successful user PIN verification"""
        # Create a user with a PIN
        user = User(
            display_name="Test User",
            email="test@example.com",
            role=UserRole.USER,
            pin_hash=UserPinService.hash_pin("1234")
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify correct PIN
        assert UserPinService.verify_user_pin(db_session, user.id, "1234") is True
        
        # Verify incorrect PIN
        assert UserPinService.verify_user_pin(db_session, user.id, "wrong") is False

    def test_verify_user_pin_inactive_user(self, db_session):
        """Test PIN verification fails for inactive user"""
        user = User(
            display_name="Inactive User",
            email="inactive@example.com",
            role=UserRole.USER,
            is_active=False,
            pin_hash=UserPinService.hash_pin("1234")
        )
        db_session.add(user)
        db_session.commit()
        
        # Should fail for inactive user even with correct PIN
        assert UserPinService.verify_user_pin(db_session, user.id, "1234") is False

    def test_change_user_pin_success(self, db_session):
        """Test successful PIN change"""
        user = User(
            display_name="Test User",
            email="change@example.com",
            role=UserRole.USER,
            pin_hash=UserPinService.hash_pin("1234")
        )
        db_session.add(user)
        db_session.commit()
        
        # Change PIN with correct current PIN
        result = UserPinService.change_user_pin(db_session, user.id, "1234", "5678", user.id)
        assert result is True
        
        # Verify old PIN no longer works
        assert UserPinService.verify_user_pin(db_session, user.id, "1234") is False
        
        # Verify new PIN works
        assert UserPinService.verify_user_pin(db_session, user.id, "5678") is True

    def test_change_user_pin_wrong_current(self, db_session):
        """Test PIN change fails with wrong current PIN"""
        user = User(
            display_name="Test User",
            email="wrong@example.com",
            role=UserRole.USER,
            pin_hash=UserPinService.hash_pin("1234")
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to change PIN with wrong current PIN
        result = UserPinService.change_user_pin(db_session, user.id, "wrong", "5678", user.id)
        assert result is False
        
        # Verify original PIN still works
        assert UserPinService.verify_user_pin(db_session, user.id, "1234") is True

    def test_set_user_pin_admin(self, db_session):
        """Test admin setting user PIN without current PIN"""
        user = User(
            display_name="Test User",
            email="admin@example.com",
            role=UserRole.USER,
            pin_hash=UserPinService.hash_pin("1234")
        )
        db_session.add(user)
        db_session.commit()
        
        # Create an admin user for the audit log
        admin = User(
            display_name="Admin User",
            email="admin2@example.com",
            role=UserRole.TREASURER,
            pin_hash=UserPinService.hash_pin("adminpin")
        )
        db_session.add(admin)
        db_session.commit()
        
        # Admin can set PIN without knowing current PIN
        result = UserPinService.set_user_pin(db_session, user.id, "newpin", admin.id)
        assert result is True
        
        # Verify new PIN works
        assert UserPinService.verify_user_pin(db_session, user.id, "newpin") is True
        
        # Verify old PIN no longer works
        assert UserPinService.verify_user_pin(db_session, user.id, "1234") is False