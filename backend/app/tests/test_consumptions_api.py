"""Test consumption API endpoints (updated for admin wrapper + treasurer headers)."""
import pytest
from uuid import uuid4


def _wrapper(admin_bootstrap, user_sub_payload: dict):
    return {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": user_sub_payload,
    }


@pytest.fixture
def test_user(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Test User",
        "role": "user",
        "is_active": True,
        "pin": "testpin123"
    })
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def test_treasurer(client, admin_bootstrap):
    treasurer_pin = "treasurerPIN123"
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Test Treasurer",
        "role": "treasurer",
        "is_active": True,
        "pin": treasurer_pin
    })
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    data["_headers"] = {"x-actor-id": data["id"], "x-actor-pin": treasurer_pin}
    return data


@pytest.fixture
def test_product(client, test_treasurer):
    import time
    product_data = {
        "name": f"Coffee {int(time.time()*1000)}",
        "price_cents": 150,
        "is_active": True
    }
    response = client.post("/products/", json=product_data, headers=test_treasurer["_headers"])
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def sample_consumption_data(test_user, test_product):
    return {"user_id": test_user["id"], "product_id": test_product["id"], "qty": 2}


def test_create_consumption(client, test_user, test_product, test_treasurer, sample_consumption_data):
    response = client.post("/consumptions/", json=sample_consumption_data, headers=test_treasurer["_headers"])
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
    consumption_data = {
        "user_id": str(uuid4()),
        "product_id": test_product["id"],
        "qty": 1
    }
    response = client.post("/consumptions/", json=consumption_data, headers=test_treasurer["_headers"])
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_create_consumption_product_not_found(client, test_user, test_treasurer):
    consumption_data = {
        "user_id": test_user["id"],
        "product_id": str(uuid4()),
        "qty": 1
    }
    response = client.post("/consumptions/", json=consumption_data, headers=test_treasurer["_headers"])
    assert response.status_code == 404
    assert "Product not found or inactive" in response.json()["detail"]


def test_get_consumptions(client, test_user, test_product, test_treasurer, sample_consumption_data):
    client.post("/consumptions/", json=sample_consumption_data, headers=test_treasurer["_headers"])
    
    response = client.get("/consumptions/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == sample_consumption_data["user_id"]


def test_get_consumptions_with_filters(client, test_user, test_product, test_treasurer, sample_consumption_data):
    client.post("/consumptions/", json=sample_consumption_data, headers=test_treasurer["_headers"])
    
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
    create_response = client.post("/consumptions/", json=sample_consumption_data, headers=test_treasurer["_headers"])
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
    import time
    for i in range(3):
        consumption_data = sample_consumption_data.copy()
        consumption_data["qty"] = i + 1
        client.post("/consumptions/", json=consumption_data, headers=test_treasurer["_headers"])
        time.sleep(0.002)
    
    response = client.get(f"/consumptions/user/{test_user['id']}/recent?limit=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    # Should be ordered by most recent first
    assert data[0]["qty"] == 3  # Last created
    assert data[1]["qty"] == 2  # Second to last


def test_get_user_recent_consumptions_limit(client, test_user, test_product, test_treasurer, sample_consumption_data):
    for i in range(5):
        consumption_data = sample_consumption_data.copy()
        consumption_data["qty"] = i + 1
        client.post("/consumptions/", json=consumption_data, headers=test_treasurer["_headers"])
    
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