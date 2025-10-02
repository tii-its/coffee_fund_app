"""
Test user deletion functionality with admin PIN requirements.
"""
import pytest
from uuid import uuid4


def test_delete_user_requires_admin_headers(client, test_user):
    """Test that user deletion requires admin headers."""
    user_id = test_user["id"]
    
    # Try to delete without headers
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 422  # Validation error for missing headers
    assert "Field required" in response.json()["detail"][0]["msg"]


def test_delete_user_requires_valid_admin_id(client, test_user):
    """Test that user deletion requires a valid admin user ID."""
    user_id = test_user["id"]
    fake_admin_id = str(uuid4())
    
    # Try to delete with fake admin ID
    response = client.delete(
        f"/users/{user_id}",
        headers={"x-actor-id": fake_admin_id, "x-actor-pin": "9999"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Actor not found"


def test_delete_user_requires_admin_role(client, test_user, treasurer_context):
    """Test that user deletion requires admin role, not just treasurer."""
    user_id = test_user["id"]
    treasurer_headers = treasurer_context["headers"]
    
    # Try to delete with treasurer credentials (should fail - only admin allowed)
    response = client.delete(f"/users/{user_id}", headers=treasurer_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Actor is not an admin"


def test_delete_user_requires_correct_admin_pin(client, test_user, admin_bootstrap):
    """Test that user deletion requires correct admin PIN."""
    user_id = test_user["id"]
    admin_id = admin_bootstrap["id"]
    
    # Try to delete with wrong PIN
    response = client.delete(
        f"/users/{user_id}",
        headers={"x-actor-id": admin_id, "x-actor-pin": "wrong-pin"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin PIN"


def test_delete_user_success_with_valid_admin_credentials(client, test_user, admin_headers):
    """Test successful user deletion with valid admin credentials."""
    user_id = test_user["id"]
    
    # Verify user exists first
    response = client.get("/users/")
    assert response.status_code == 200
    users_before = response.json()
    user_exists = any(u["id"] == user_id for u in users_before)
    assert user_exists, "Test user should exist before deletion"
    
    # Delete user with valid admin credentials
    response = client.delete(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "User permanently deleted"
    
    # Verify user is fully removed
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 404


def test_delete_nonexistent_user(client, admin_headers):
    """Test deletion of non-existent user."""
    fake_user_id = str(uuid4())
    
    response = client.delete(f"/users/{fake_user_id}", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_delete_user_creates_audit_entry(client, test_user, admin_bootstrap, admin_headers):
    """Test that user deletion creates an audit entry."""
    user_id = test_user["id"]
    admin_id = admin_bootstrap["id"]
    
    # Delete user
    response = client.delete(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    
    # Check audit entries
    response = client.get("/audit/", params={"entity": "user", "entity_id": user_id})
    assert response.status_code == 200
    audit_entries = response.json()
    
    # Find the delete audit entry
    delete_entry = next((entry for entry in audit_entries if entry["action"] == "delete"), None)
    assert delete_entry is not None, "Delete action should be audited"
    assert delete_entry["actor_id"] == admin_id
    assert delete_entry["entity"] == "user"
    assert delete_entry["entity_id"] == user_id
    assert delete_entry["meta_json"]["hard_delete"] is True


def test_delete_user_multiple_users_isolation(client, admin_bootstrap, admin_headers):
    """Test that deleting one user doesn't affect others."""
    # Create two test users
    user1_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": "Test User 1",
            "role": "user",
            "is_active": True,
            "pin": "pin1"
        }
    }
    user2_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": {
            "display_name": "Test User 2",
            "role": "user",
            "is_active": True,
            "pin": "pin2"
        }
    }
    
    response1 = client.post("/users/", json=user1_payload)
    response2 = client.post("/users/", json=user2_payload)
    assert response1.status_code == 201
    assert response2.status_code == 201
    
    user1_id = response1.json()["id"]
    user2_id = response2.json()["id"]
    
    # Delete first user
    response = client.delete(f"/users/{user1_id}", headers=admin_headers)
    assert response.status_code == 200
    
    # Verify second user still retrievable
    response = client.get(f"/users/{user2_id}", headers=admin_headers)
    assert response.status_code == 200
    # First user should 404
    response = client.get(f"/users/{user1_id}", headers=admin_headers)
    assert response.status_code == 404


def test_admin_cannot_delete_themselves(client, admin_bootstrap, admin_headers):
    """Test that admin users cannot delete themselves."""
    admin_id = admin_bootstrap["id"]
    
    # Try to delete self
    response = client.delete(f"/users/{admin_id}", headers=admin_headers)
    # This should either succeed (soft delete) or fail with a specific error
    # For now, let's test that the operation is handled gracefully
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete the last remaining admin user"