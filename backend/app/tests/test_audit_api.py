"""
Test audit API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
from app.services.audit import AuditService
from uuid import uuid4

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


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
    """Create a sample audit entry"""
    db = next(override_get_db())
    try:
        audit_entry = AuditService.log_action(
            db=db,
            actor_id=test_user["id"],
            action="create",
            entity="test_entity",
            entity_id=uuid4(),
            meta_data={"test": "data"}
        )
        return {
            "id": str(audit_entry.id),
            "actor_id": str(audit_entry.actor_id),
            "action": audit_entry.action,
            "entity": audit_entry.entity,
            "entity_id": str(audit_entry.entity_id)
        }
    finally:
        db.close()


def test_get_audit_entries(client, sample_audit_entry):
    """Test getting all audit entries"""
    response = client.get("/audit/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Find our audit entry
    audit_entry = next((entry for entry in data if entry["id"] == sample_audit_entry["id"]), None)
    assert audit_entry is not None
    assert audit_entry["action"] == "create"
    assert audit_entry["entity"] == "test_entity"


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
    # Create multiple audit entries
    db = next(override_get_db())
    try:
        for i in range(5):
            AuditService.log_action(
                db=db,
                actor_id=test_user["id"],
                action="create",
                entity=f"entity_{i}",
                entity_id=uuid4(),
                meta_data={"index": i}
            )
    finally:
        db.close()
    
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
    # Create multiple audit entries
    db = next(override_get_db())
    entry_ids = []
    try:
        for i in range(3):
            entry = AuditService.log_action(
                db=db,
                actor_id=test_user["id"],
                action="create",
                entity=f"entity_{i}",
                entity_id=uuid4(),
                meta_data={"order": i}
            )
            entry_ids.append(str(entry.id))
    finally:
        db.close()
    
    response = client.get("/audit/")
    assert response.status_code == 200
    data = response.json()
    
    # Find our entries and check they're in reverse order (newest first)
    our_entries = [entry for entry in data if entry["id"] in entry_ids]
    assert len(our_entries) == 3
    
    # The entries should be ordered by creation time (newest first)
    # Since we created them in sequence, the last one created should be first
    assert our_entries[0]["meta_json"]["order"] == 2
    assert our_entries[1]["meta_json"]["order"] == 1
    assert our_entries[2]["meta_json"]["order"] == 0