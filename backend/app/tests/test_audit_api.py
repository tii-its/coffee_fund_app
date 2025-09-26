"""
Test audit API endpoints
"""
import pytest
from app.services.audit import AuditService
from uuid import uuid4


@pytest.fixture
def test_user(client):
    """Create a test user"""
    user_data = {
        "display_name": "Test User",
        "role": "user",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    return response.json()


@pytest.fixture
def sample_audit_entry(client, test_user):
    """Create a sample audit entry by creating a user (which triggers audit log)"""
    # Creating a user triggers an audit entry via the API
    user_data = {
        "display_name": "Audit Test User",
        "role": "user",
        "is_active": True
    }
    response = client.post(f"/users/?creator_id={test_user['id']}", json=user_data)
    created_user = response.json()
    
    # The audit entry was created automatically by the user creation
    # We'll return info to identify it in tests
    return {
        "actor_id": test_user["id"],
        "action": "create", 
        "entity": "user",
        "entity_id": created_user["id"]
    }


def test_get_audit_entries(client, sample_audit_entry):
    """Test getting all audit entries"""
    response = client.get("/audit/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Find our audit entry (there will be at least one from user creation)
    audit_entry = next((entry for entry in data if entry["action"] == "create" and entry["entity"] == "user"), None)
    assert audit_entry is not None
    assert audit_entry["action"] == "create"
    assert audit_entry["entity"] == "user"


def test_get_audit_entries_with_actor_filter(client, test_user, sample_audit_entry):
    """Test filtering audit entries by actor"""
    response = client.get(f"/audit/?actor_id={test_user['id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    for entry in data:
        assert entry["actor_id"] == test_user["id"]


def test_get_audit_entries_with_entity_filter(client, sample_audit_entry):
    """Test filtering audit entries by entity"""
    response = client.get("/audit/?entity=test_entity")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    for entry in data:
        assert entry["entity"] == "test_entity"


def test_get_audit_entries_with_entity_id_filter(client, sample_audit_entry):
    """Test filtering audit entries by entity_id"""
    response = client.get(f"/audit/?entity_id={sample_audit_entry['entity_id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["entity_id"] == sample_audit_entry["entity_id"]


def test_get_audit_entries_pagination(client, test_user):
    """Test audit entries pagination"""
    # Create multiple users to generate audit entries
    for i in range(5):
        user_data = {
            "display_name": f"Pagination User {i}",
            "role": "user",
            "is_active": True
        }
        client.post(f"/users/?creator_id={test_user['id']}", json=user_data)
    
    # Test pagination
    response = client.get("/audit/?skip=0&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    response = client.get("/audit/?skip=3&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least 2 more from our created entries


def test_get_audit_entry_by_id(client, sample_audit_entry):
    """Test getting specific audit entry"""
    response = client.get(f"/audit/{sample_audit_entry['id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_audit_entry["id"]
    assert data["action"] == "create"
    assert data["entity"] == "test_entity"


def test_get_audit_entry_by_id_not_found(client):
    """Test getting non-existent audit entry"""
    response = client.get(f"/audit/{uuid4()}")
    assert response.status_code == 404
    assert "Audit entry not found" in response.json()["detail"]


def test_audit_entries_ordered_by_date(client, test_user):
    """Test that audit entries are ordered by date (newest first)"""
    # Create multiple users to generate audit entries with timestamps
    entry_names = []
    for i in range(3):
        user_data = {
            "display_name": f"Order User {i}",
            "role": "user", 
            "is_active": True
        }
        response = client.post(f"/users/?creator_id={test_user['id']}", json=user_data)
        entry_names.append(user_data["display_name"])
    
    response = client.get("/audit/")
    assert response.status_code == 200
    data = response.json()
    
    # Find entries related to our created users and check they're in reverse order (newest first)
    our_entries = [entry for entry in data if entry["action"] == "create" and entry["entity"] == "user"]
    assert len(our_entries) >= 3
    
    # The entries should be ordered by creation time (newest first)
    # Check that timestamps are in descending order
    for i in range(len(our_entries) - 1):
        assert our_entries[i]["at"] >= our_entries[i + 1]["at"]