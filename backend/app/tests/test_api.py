import pytest


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/settings/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_settings(client):
    """Test settings endpoint"""
    response = client.get("/settings/")
    assert response.status_code == 200
    data = response.json()
    assert "threshold_cents" in data
    assert "csv_export_limit" in data


def test_create_user(client, sample_user_data, admin_bootstrap):
    """Test user creation via admin wrapper."""
    payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": sample_user_data
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["display_name"] == sample_user_data["display_name"]
    assert data["role"] == sample_user_data["role"]
    assert "id" in data


def test_get_users(client, sample_user_data, admin_bootstrap):
    """Test getting users (admin only)."""
    create_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": sample_user_data
    }
    client.post("/users/", json=create_payload)
    response = client.get("/users/", headers={"x-actor-id": admin_bootstrap["id"], "x-actor-pin": admin_bootstrap["pin"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list) and len(data) > 0


def test_create_product(client, sample_product_data, treasurer_context):
    """Test product creation (treasurer headers required)."""
    response = client.post("/products/", json=sample_product_data, headers=treasurer_context["headers"])
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == sample_product_data["name"]
    assert data["price_cents"] == sample_product_data["price_cents"]
    assert "id" in data


def test_get_products(client, sample_product_data, treasurer_context):
    """Test getting products"""
    client.post("/products/", json=sample_product_data, headers=treasurer_context["headers"])    
    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) > 0


def test_get_users_above_threshold(client):
    """Test getting users with balance above threshold via API"""
    # Test the new above-threshold endpoint
    response = client.get("/users/balances/above-threshold?threshold_cents=1000")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should be empty initially since no users have balances set up
    assert len(data) == 0


def test_get_users_below_threshold(client):
    """Test getting users with balance below threshold via API"""
    # Test the existing below-threshold endpoint
    response = client.get("/users/balances/below-threshold?threshold_cents=1000")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_delete_user_hard_delete(client, sample_user_data, admin_bootstrap):
    """Ensure deleting a user removes it permanently when no related records exist."""
    # Create user
    create_payload = {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": sample_user_data
    }
    create_resp = client.post("/users/", json=create_payload)
    assert create_resp.status_code == 201, create_resp.text
    user_id = create_resp.json()["id"]

    # Delete user
    del_resp = client.delete(f"/users/{user_id}", headers={"x-actor-id": admin_bootstrap["id"], "x-actor-pin": admin_bootstrap["pin"]})
    assert del_resp.status_code == 200, del_resp.text
    assert del_resp.json()["message"] == "User permanently deleted"

    # Subsequent get should 404
    get_resp = client.get(f"/users/{user_id}", headers={"x-actor-id": admin_bootstrap["id"], "x-actor-pin": admin_bootstrap["pin"]})
    assert get_resp.status_code == 404


def test_delete_last_admin_forbidden(client, admin_bootstrap):
    """Attempting to delete the only existing admin should be blocked."""
    admin_id = admin_bootstrap["id"]
    resp = client.delete(f"/users/{admin_id}", headers={"x-actor-id": admin_id, "x-actor-pin": admin_bootstrap["pin"]})
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"] == "Cannot delete the last remaining admin user"


def test_verify_user_pin_success(client, admin_bootstrap):
    """Verify endpoint returns 200 for correct PIN of existing user."""
    payload = {
        "user_id": admin_bootstrap["id"],
        "pin": admin_bootstrap["pin"],
    }
    resp = client.post("/users/verify-user-pin", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["message"].lower().startswith("user pin verified")


def test_verify_user_pin_invalid_pin(client, admin_bootstrap):
    """Verify endpoint returns 403 for wrong PIN."""
    payload = {
        "user_id": admin_bootstrap["id"],
        "pin": "wrongpin",
    }
    resp = client.post("/users/verify-user-pin", json=payload)
    assert resp.status_code == 403, resp.text
    detail = resp.json().get("detail")
    assert detail == "Invalid user PIN"


def test_verify_user_pin_unknown_user(client):
    """Verify endpoint returns 403 for unknown user id (treated as invalid)."""
    import uuid
    payload = {
        "user_id": str(uuid.uuid4()),
        "pin": "doesntmatter",
    }
    resp = client.post("/users/verify-user-pin", json=payload)
    # Service returns False leading to 403 Invalid user PIN
    assert resp.status_code == 403, resp.text
    assert resp.json().get("detail") == "Invalid user PIN"


def test_change_user_pin_success(client, admin_bootstrap):
    """End-to-end: verify old PIN works, change PIN, old fails, new works."""
    user_id = admin_bootstrap["id"]
    old_pin = admin_bootstrap["pin"]
    new_pin = "NewSecretPin456"

    # Sanity: old pin verifies
    resp_old = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": old_pin})
    assert resp_old.status_code == 200, resp_old.text

    # Change pin
    change_payload = {"user_id": user_id, "current_pin": old_pin, "new_pin": new_pin}
    change_resp = client.post("/users/change-user-pin", json=change_payload)
    assert change_resp.status_code == 200, change_resp.text
    assert "changed" in change_resp.json()["message"].lower()

    # Old pin now fails
    resp_old_fail = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": old_pin})
    assert resp_old_fail.status_code == 403

    # New pin succeeds
    resp_new = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": new_pin})
    assert resp_new.status_code == 200

    # Revert for idempotency (change back) to not affect potential later tests expecting original admin pin
    revert_payload = {"user_id": user_id, "current_pin": new_pin, "new_pin": old_pin}
    revert_resp = client.post("/users/change-user-pin", json=revert_payload)
    assert revert_resp.status_code == 200, revert_resp.text

    # Confirm revert
    resp_revert = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": old_pin})
    assert resp_revert.status_code == 200