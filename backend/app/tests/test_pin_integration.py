import hashlib
from uuid import uuid4
from app.services.pin import PinService
from app.models.users import User
from app.core.enums import UserRole


def test_pin_hash_is_stable():
    pin = "1234"
    h1 = PinService.hash_pin(pin)
    h2 = PinService.hash_pin(pin)
    assert h1 == h2 == hashlib.sha256(pin.encode()).hexdigest()


def test_verify_user_pin_roundtrip(db_session):
    user = User(display_name="PIN User", role=UserRole.USER, pin_hash=PinService.hash_pin("abc123"))
    db_session.add(user)
    db_session.commit()
    assert PinService.verify_user_pin(user.id, "abc123", db_session) is True
    assert PinService.verify_user_pin(user.id, "wrong", db_session) is False


def test_set_and_change_user_pin(db_session):
    user = User(display_name="Changer", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    assert PinService.set_user_pin(user.id, "first", db_session) is True
    assert PinService.verify_user_pin(user.id, "first", db_session) is True
    assert PinService.change_user_pin(user.id, "first", "second", db_session) is True
    assert PinService.verify_user_pin(user.id, "first", db_session) is False
    assert PinService.verify_user_pin(user.id, "second", db_session) is True


def test_verify_nonexistent_user_returns_false(db_session):
    assert PinService.verify_user_pin(uuid4(), "whatever", db_session) is False