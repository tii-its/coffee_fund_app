import pytest
from uuid import uuid4
from app.core.config import settings


def test_verify_pin_success(client):
    """Test successful PIN verification"""
    response = client.post("/users/verify-pin", json={"pin": settings.admin_pin})
    assert response.status_code == 200
    assert response.json()["message"] == "PIN verified successfully"


def test_verify_pin_failure(client):
    """Test failed treasurer PIN verification"""
    response = client.post("/users/verify-pin", json={"pin": "wrong-pin"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid PIN"


def test_create_user_with_pin(client):
    """Test creating a regular user with PIN"""
    import time
    user_data = {
        "display_name": "Test User",
        "email": f"test.user.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "user123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # Verify user PIN works
    pin_verify_response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "user123"
    })
    assert pin_verify_response.status_code == 200
    assert pin_verify_response.json()["message"] == "User PIN verified successfully"


def test_create_user_without_pin_fails(client):
    """Test creating user without PIN fails"""
    import time
    user_data = {
        "display_name": "Test User",
        "email": f"test.no.pin.{int(time.time()*1000)}@example.com",
        "role": "user"
        # No PIN provided
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422  # Validation error due to missing required PIN


def test_create_treasurer_with_treasurer_pin(client):
    """Test creating treasurer with valid treasurer PIN"""
    import time
    user_data = {
        "display_name": "Test Treasurer",
        "email": f"test.treasurer.{int(time.time()*1000)}@example.com",
        "role": "treasurer",
        "pin": settings.treasurer_pin
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201


def test_create_treasurer_with_invalid_pin_fails(client):
    """Test creating treasurer with invalid treasurer PIN fails"""
    import time
    user_data = {
        "display_name": "Test Treasurer",
        "email": f"test.treasurer.invalid.{int(time.time()*1000)}@example.com",
        "role": "treasurer",
        "pin": "wrong-treasurer-pin"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid treasurer PIN"


def test_verify_user_pin_success(client):
    """Test successful user PIN verification"""
    # First create a user
    import time
    user_data = {
        "display_name": "PIN Test User",
        "email": f"pin.test.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "userpin456"
    }
    create_response = client.post("/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Verify PIN
    response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "userpin456"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "User PIN verified successfully"


def test_verify_user_pin_failure(client):
    """Test failed user PIN verification"""
    # First create a user
    import time
    user_data = {
        "display_name": "PIN Test User",
        "email": f"pin.test.fail.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "userpin789"
    }
    create_response = client.post("/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Try to verify with wrong PIN
    response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "wrong-pin"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid user PIN"


def test_change_user_pin(client):
    """Test changing user PIN"""
    # First create a user
    import time
    user_data = {
        "display_name": "PIN Change User",
        "email": f"pin.change.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "oldpin123"
    }
    create_response = client.post("/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Change PIN
    response = client.post("/users/change-user-pin", json={
        "user_id": user_id,
        "current_pin": "oldpin123",
        "new_pin": "newpin456"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "User PIN changed successfully"
    
    # Verify old PIN no longer works
    old_pin_response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "oldpin123"
    })
    assert old_pin_response.status_code == 403
    
    # Verify new PIN works
    new_pin_response = client.post("/users/verify-user-pin", json={
        "user_id": user_id,
        "pin": "newpin456"
    })
    assert new_pin_response.status_code == 200


def test_change_user_pin_with_wrong_current_pin(client):
    """Test changing user PIN with wrong current PIN"""
    # First create a user
    import time
    user_data = {
        "display_name": "PIN Change Fail User",
        "email": f"pin.change.fail.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "correctpin"
    }
    create_response = client.post("/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Try to change PIN with wrong current PIN
    response = client.post("/users/change-user-pin", json={
        "user_id": user_id,
        "current_pin": "wrong-current-pin",
        "new_pin": "newpin456"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid current PIN"


def test_update_user_with_valid_pin(client, sample_user_data):
    """Test user update with valid PIN"""
    # First create a user
    import time
    sample_user_data = {**sample_user_data, "email": f"pin.valid.{int(time.time()*1000)}@example.com"}
    create_response = client.post("/users/", json={"user": sample_user_data, "pin": settings.admin_pin})
    # Creation endpoint returns 201 Created
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Update with valid PIN
    update_payload = {
        "user_update": {"display_name": "Updated Name"},
        "pin": settings.admin_pin
    }
    response = client.put(f"/users/{user_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Name"


def test_update_user_with_invalid_pin(client, sample_user_data):
    """Test user update with invalid PIN"""
    # First create a user
    import time
    sample_user_data = {**sample_user_data, "email": f"pin.invalid.{int(time.time()*1000)}@example.com"}
    create_response = client.post("/users/", json={"user": sample_user_data, "pin": settings.admin_pin})
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Try to update with invalid PIN
    update_payload = {
        "user_update": {"display_name": "Updated Name"},
        "pin": "wrong-pin"
    }
    response = client.put(f"/users/{user_id}", json=update_payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid PIN"


def test_delete_user_with_valid_pin(client, sample_user_data):
    """Test user deletion with valid PIN"""
    # First create a user
    import time
    sample_user_data = {**sample_user_data, "email": f"pin.delete.valid.{int(time.time()*1000)}@example.com"}
    create_response = client.post("/users/", json={"user": sample_user_data, "pin": settings.admin_pin})
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Delete with valid PIN
    response = client.request("DELETE", f"/users/{user_id}", json={"pin": settings.admin_pin})
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    
    # Verify user is marked as inactive (soft delete)
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


def test_delete_user_with_invalid_pin(client, sample_user_data):
    """Test user deletion with invalid PIN"""
    # First create a user
    import time
    sample_user_data = {**sample_user_data, "email": f"pin.delete.invalid.{int(time.time()*1000)}@example.com"}
    create_response = client.post("/users/", json={"user": sample_user_data, "pin": settings.admin_pin})
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    
    # Try to delete with invalid PIN
    response = client.request("DELETE", f"/users/{user_id}", json={"pin": "wrong-pin"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid PIN"


def test_change_pin(client):
    """Test PIN change functionality"""
    response = client.post("/users/change-pin", json={
    "current_pin": settings.admin_pin,
        "new_pin": "new-pin-123"
    })
    assert response.status_code == 200
    # Implementation returns a direct success message
    assert "PIN changed successfully" in response.json()["message"]


def test_change_pin_with_wrong_current_pin(client):
    """Test PIN change with wrong current PIN"""
    response = client.post("/users/change-pin", json={
        "current_pin": "wrong-pin",
        "new_pin": "new-pin-123"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid current PIN"