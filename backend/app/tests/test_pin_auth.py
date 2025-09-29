import pytest
from uuid import uuid4
from app.core.config import settings  # retained for future use if needed


# Global verify-pin / change-pin endpoints have been removed. Tests below focus solely
# on per-user PIN behaviors (creation requires PIN, verification, change, auth failures).


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


# Treasurer creation now uses its own per-user PIN like any other user.
def test_create_treasurer(client):
    import time
    treasurer_pin = "treasurer123"
    user_data = {
        "display_name": "Test Treasurer",
        "email": f"test.treasurer.{int(time.time()*1000)}@example.com",
        "role": "treasurer",
        "pin": treasurer_pin
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    treasurer_id = response.json()["id"]
    # Verify treasurer's own PIN works
    verify = client.post("/users/verify-user-pin", json={"user_id": treasurer_id, "pin": treasurer_pin})
    assert verify.status_code == 200


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


def test_update_user(client):
    import time
    create_payload = {
        "display_name": "Updatable User",
        "email": f"update.user.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "origpin"
    }
    create_response = client.post("/users/", json=create_payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    update_payload = {"user_update": {"display_name": "Updated Name"}}
    response = client.put(f"/users/{user_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Name"


# Invalid update PIN test removed (no global PIN verification now).


def test_delete_user(client):
    import time
    payload = {
        "display_name": "Deletable User",
        "email": f"delete.user.{int(time.time()*1000)}@example.com",
        "role": "user",
        "pin": "delpin"
    }
    create_response = client.post("/users/", json=payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    response = client.request("DELETE", f"/users/{user_id}")
    assert response.status_code == 200
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


# Invalid delete PIN test removed.


# Global PIN change tests removed (feature deprecated).