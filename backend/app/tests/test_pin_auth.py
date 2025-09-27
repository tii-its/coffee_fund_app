import pytest
from uuid import uuid4
from app.core.config import settings


def test_verify_pin_success(client):
    """Test successful PIN verification"""
    response = client.post("/users/verify-pin", json={"pin": settings.treasurer_pin})
    assert response.status_code == 200
    assert response.json()["message"] == "PIN verified successfully"


def test_verify_pin_failure(client):
    """Test failed PIN verification"""
    response = client.post("/users/verify-pin", json={"pin": "wrong-pin"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid PIN"


def test_update_user_with_valid_pin(client, sample_user_data):
    """Test user update with valid PIN"""
    # First create a user
    create_response = client.post("/users/", json=sample_user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]
    
    # Update with valid PIN
    update_data = {
        "display_name": "Updated Name",
        "pin": settings.treasurer_pin
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Name"


def test_update_user_with_invalid_pin(client, sample_user_data):
    """Test user update with invalid PIN"""
    # First create a user
    create_response = client.post("/users/", json=sample_user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]
    
    # Try to update with invalid PIN
    update_data = {
        "display_name": "Updated Name",
        "pin": "wrong-pin"
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid PIN"


def test_delete_user_with_valid_pin(client, sample_user_data):
    """Test user deletion with valid PIN"""
    # First create a user
    create_response = client.post("/users/", json=sample_user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]
    
    # Delete with valid PIN
    response = client.delete(f"/users/{user_id}", json={"pin": settings.treasurer_pin})
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    
    # Verify user is marked as inactive (soft delete)
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


def test_delete_user_with_invalid_pin(client, sample_user_data):
    """Test user deletion with invalid PIN"""
    # First create a user
    create_response = client.post("/users/", json=sample_user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]
    
    # Try to delete with invalid PIN
    response = client.delete(f"/users/{user_id}", json={"pin": "wrong-pin"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid PIN"


def test_change_pin(client):
    """Test PIN change functionality"""
    response = client.post("/users/change-pin", json={
        "current_pin": settings.treasurer_pin,
        "new_pin": "new-pin-123"
    })
    assert response.status_code == 200
    assert "PIN change requested successfully" in response.json()["message"]


def test_change_pin_with_wrong_current_pin(client):
    """Test PIN change with wrong current PIN"""
    response = client.post("/users/change-pin", json={
        "current_pin": "wrong-pin",
        "new_pin": "new-pin-123"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid current PIN"