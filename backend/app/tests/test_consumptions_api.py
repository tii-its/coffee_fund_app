"""
Test consumption API endpoints
"""
import pytest
from app.models import User, Product
from app.core.enums import UserRole
from app.core.config import settings
from uuid import uuid4


@pytest.fixture
def test_user(client):
    """Create a test user"""
    import time
    user_data = {
        "display_name": "Test User",
        "email": f"consumption.test.user.{int(time.time()*1000)}@example.com",
        "role": "user",
        "is_active": True
    }
    response = client.post("/users/", json={"user": user_data, "pin": settings.admin_pin})
    return response.json()


@pytest.fixture
def test_treasurer(client):
    """Create a test treasurer"""
    import time
    user_data = {
        "display_name": "Test Treasurer", 
        "email": f"consumption.test.treasurer.{int(time.time()*1000)}@example.com",
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json={"user": user_data, "pin": settings.admin_pin})
    return response.json()


@pytest.fixture
def test_product(client):
    """Create a test product"""
    import time
    product_data = {
        "name": f"Coffee {int(time.time()*1000)}",
        "price_cents": 150,
        "is_active": True
    }
    response = client.post("/products/", json=product_data)
    return response.json()


@pytest.fixture
def sample_consumption_data(test_user, test_product):
    """Sample consumption data"""
    return {
        "user_id": test_user["id"],
        "product_id": test_product["id"],
        "qty": 2
    }


def test_create_consumption(client, test_user, test_product, test_treasurer, sample_consumption_data):
    """Test consumption creation"""
    response = client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=sample_consumption_data
    )
    assert response.status_code == 201
    
    data = response.json()
    assert data["user_id"] == sample_consumption_data["user_id"]
    assert data["product_id"] == sample_consumption_data["product_id"]
    assert data["qty"] == sample_consumption_data["qty"]
    assert data["unit_price_cents"] == 150
    assert data["amount_cents"] == 300  # 2 * 150
    assert "id" in data
    assert "at" in data


def test_create_consumption_user_not_found(client, test_product, test_treasurer):
    """Test consumption creation with invalid user"""
    consumption_data = {
        "user_id": str(uuid4()),
        "product_id": test_product["id"],
        "qty": 1
    }
    response = client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=consumption_data
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_create_consumption_product_not_found(client, test_user, test_treasurer):
    """Test consumption creation with invalid product"""
    consumption_data = {
        "user_id": test_user["id"],
        "product_id": str(uuid4()),
        "qty": 1
    }
    response = client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=consumption_data
    )
    assert response.status_code == 404
    assert "Product not found or inactive" in response.json()["detail"]


def test_get_consumptions(client, test_user, test_product, test_treasurer, sample_consumption_data):
    """Test getting all consumptions"""
    # Create a consumption first
    client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=sample_consumption_data
    )
    
    response = client.get("/consumptions/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == sample_consumption_data["user_id"]


def test_get_consumptions_with_filters(client, test_user, test_product, test_treasurer, sample_consumption_data):
    """Test getting consumptions with filters"""
    # Create a consumption
    client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=sample_consumption_data
    )
    
    # Filter by user_id
    response = client.get(f"/consumptions/?user_id={test_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    # Filter by product_id
    response = client.get(f"/consumptions/?product_id={test_product['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    # Filter by non-existent user
    response = client.get(f"/consumptions/?user_id={uuid4()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_get_consumption_by_id(client, test_user, test_product, test_treasurer, sample_consumption_data):
    """Test getting specific consumption"""
    # Create a consumption
    create_response = client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=sample_consumption_data
    )
    consumption_id = create_response.json()["id"]
    
    response = client.get(f"/consumptions/{consumption_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == consumption_id
    assert data["user_id"] == sample_consumption_data["user_id"]


def test_get_consumption_by_id_not_found(client):
    """Test getting non-existent consumption"""
    response = client.get(f"/consumptions/{uuid4()}")
    assert response.status_code == 404
    assert "Consumption not found" in response.json()["detail"]


def test_get_user_recent_consumptions(client, test_user, test_product, test_treasurer, sample_consumption_data):
    """Test getting recent consumptions for a user"""
    # Create multiple consumptions
    import time
    for i in range(3):
        consumption_data = sample_consumption_data.copy()
        consumption_data["qty"] = i + 1
        client.post(
            f"/consumptions/?creator_id={test_treasurer['id']}", 
            json=consumption_data
        )
        # Ensure distinct timestamps for deterministic ordering
        time.sleep(0.002)
    
    response = client.get(f"/consumptions/user/{test_user['id']}/recent?limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    # Should be ordered by most recent first
    assert data[0]["qty"] == 3  # Last created
    assert data[1]["qty"] == 2  # Second to last


def test_get_user_recent_consumptions_limit(client, test_user, test_product, test_treasurer, sample_consumption_data):
    """Test limit parameter for recent consumptions"""
    # Create 5 consumptions
    for i in range(5):
        consumption_data = sample_consumption_data.copy()
        consumption_data["qty"] = i + 1
        client.post(
            f"/consumptions/?creator_id={test_treasurer['id']}", 
            json=consumption_data
        )
    
    # Test default limit
    response = client.get(f"/consumptions/user/{test_user['id']}/recent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # All consumptions since less than default limit
    
    # Test custom limit
    response = client.get(f"/consumptions/user/{test_user['id']}/recent?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3