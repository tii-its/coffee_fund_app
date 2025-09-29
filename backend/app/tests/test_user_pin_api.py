import pytest
from uuid import uuid4
from app.core.config import settings
from app.services.user_pin import UserPinService


def test_create_user_with_pin(client, sample_user_data):
    """Test creating a user with PIN"""
    import time
    sample_user_data = {
        **sample_user_data, 
        "email": f"pin.create.{int(time.time()*1000)}@example.com",
        "pin": "1234"
    }
    
    response = client.post("/users/", json={
        "user": sample_user_data,
        "admin_pin": settings.admin_pin
    })
    
    assert response.status_code == 201
    user_data = response.json()
    assert "pin" not in user_data  # PIN should not be returned
    assert user_data["display_name"] == sample_user_data["display_name"]


def test_create_user_missing_pin(client, sample_user_data):
    """Test creating a user without PIN fails"""
    import time
    user_data_no_pin = {
        k: v for k, v in sample_user_data.items() if k != "pin"
    }
    user_data_no_pin["email"] = f"no.pin.{int(time.time()*1000)}@example.com"
    
    response = client.post("/users/", json={
        "user": user_data_no_pin,
        "admin_pin": settings.admin_pin
    })
    
    # Should fail due to missing PIN
    assert response.status_code == 422


def test_verify_user_pin_success(client, sample_user_data):
    """Test successful user PIN verification"""
    import time
    sample_user_data = {
        **sample_user_data,
        "email": f"verify.success.{int(time.time()*1000)}@example.com",
        "pin": "1234"
    }
    
    # Create user first
    create_response = client.post("/users/", json={
        "user": sample_user_data,
        "admin_pin": settings.admin_pin
    })
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Verify PIN
    response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "1234"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User PIN verified successfully"
    assert "user" in data
    assert data["user"]["id"] == user_id


def test_verify_user_pin_failure(client, sample_user_data):
    """Test failed user PIN verification"""
    import time
    sample_user_data = {
        **sample_user_data,
        "email": f"verify.failure.{int(time.time()*1000)}@example.com",
        "pin": "1234"
    }
    
    # Create user first
    create_response = client.post("/users/", json={
        "user": sample_user_data,
        "admin_pin": settings.admin_pin
    })
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Try to verify with wrong PIN
    response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "wrong"
    })
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid user PIN"


def test_change_user_pin_success(client, sample_user_data):
    """Test successful user PIN change"""
    import time
    sample_user_data = {
        **sample_user_data,
        "email": f"change.success.{int(time.time()*1000)}@example.com",
        "pin": "1234"
    }
    
    # Create user first
    create_response = client.post("/users/", json={
        "user": sample_user_data,
        "admin_pin": settings.admin_pin
    })
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Change PIN
    response = client.post("/users/change-user-pin", json={
        "user_id": user_id,
        "current_pin": "1234",
        "new_pin": "5678"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "User PIN changed successfully"
    
    # Verify old PIN no longer works
    old_verify = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "1234"
    })
    assert old_verify.status_code == 403
    
    # Verify new PIN works
    new_verify = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "5678"
    })
    assert new_verify.status_code == 200


def test_change_user_pin_wrong_current(client, sample_user_data):
    """Test user PIN change fails with wrong current PIN"""
    import time
    sample_user_data = {
        **sample_user_data,
        "email": f"change.failure.{int(time.time()*1000)}@example.com",
        "pin": "1234"
    }
    
    # Create user first
    create_response = client.post("/users/", json={
        "user": sample_user_data,
        "admin_pin": settings.admin_pin
    })
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Try to change PIN with wrong current PIN
    response = client.post("/users/change-user-pin", json={
        "user_id": user_id,
        "current_pin": "wrong",
        "new_pin": "5678"
    })
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid current PIN or user not found"
    
    # Verify original PIN still works
    verify = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "1234"
    })
    assert verify.status_code == 200


def test_admin_pin_vs_user_pin_separation(client, sample_user_data):
    """Test that admin PIN and user PINs are separate"""
    import time
    sample_user_data = {
        **sample_user_data,
        "email": f"separation.{int(time.time()*1000)}@example.com",
        "pin": "1234"
    }
    
    # Create user with PIN different from admin PIN
    create_response = client.post("/users/", json={
        "user": sample_user_data,
        "admin_pin": settings.admin_pin
    })
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Admin PIN verification should still work
    admin_verify = client.post("/users/verify-pin", json={
        "pin": settings.admin_pin
    })
    assert admin_verify.status_code == 200
    
    # User PIN verification should work with user's PIN
    user_verify = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "1234"
    })
    assert user_verify.status_code == 200
    
    # User PIN should not work with admin PIN (unless they happen to be the same)
    if settings.admin_pin != "1234":
        wrong_verify = client.post("/users/verify-user-pin", json={
            "user_id": user_id,
            "pin": settings.admin_pin
        })
        assert wrong_verify.status_code == 403