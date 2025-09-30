import pytest

# Updated tests to use AdminUserCreateRequest wrapper and per-user PIN logic.


def _wrapper(admin_bootstrap, user_sub_payload: dict):
    return {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": user_sub_payload,
    }


def test_create_user_with_pin(client, admin_bootstrap):
    user_payload = _wrapper(admin_bootstrap, {
        "display_name": "Test User",
        "role": "user",
        "is_active": True,
        "pin": "user123"
    })
    response = client.post("/users/", json=user_payload)
    assert response.status_code == 201, response.text
    user_id = response.json()["id"]
    pin_verify_response = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": "user123"})
    assert pin_verify_response.status_code == 200
    assert pin_verify_response.json()["message"] == "User PIN verified successfully"


def test_create_user_without_pin_fails(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Test User",
        "role": "user",
        "is_active": True
        # Missing pin
    })
    response = client.post("/users/", json=payload)
    assert response.status_code == 422


def test_create_treasurer(client, admin_bootstrap):
    treasurer_pin = "treasurer123"
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Test Treasurer",
        "role": "treasurer",
        "is_active": True,
        "pin": treasurer_pin
    })
    response = client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    treasurer_id = response.json()["id"]
    verify = client.post("/users/verify-user-pin", json={"user_id": treasurer_id, "pin": treasurer_pin})
    assert verify.status_code == 200


def test_verify_user_pin_success(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "PIN Test User",
        "role": "user",
        "is_active": True,
        "pin": "userpin456"
    })
    create_response = client.post("/users/", json=payload)
    assert create_response.status_code == 201, create_response.text
    user_id = create_response.json()["id"]
    response = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": "userpin456"})
    assert response.status_code == 200
    assert response.json()["message"] == "User PIN verified successfully"


def test_verify_user_pin_failure(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "PIN Test User",
        "role": "user",
        "is_active": True,
        "pin": "userpin789"
    })
    create_response = client.post("/users/", json=payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    response = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": "wrong-pin"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid user PIN"


def test_change_user_pin(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "PIN Change User",
        "role": "user",
        "is_active": True,
        "pin": "oldpin123"
    })
    create_response = client.post("/users/", json=payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    response = client.post("/users/change-user-pin", json={"user_id": user_id, "current_pin": "oldpin123", "new_pin": "newpin456"})
    assert response.status_code == 200
    assert response.json()["message"] == "User PIN changed successfully"
    old_pin_response = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": "oldpin123"})
    assert old_pin_response.status_code == 403
    new_pin_response = client.post("/users/verify-user-pin", json={"user_id": user_id, "pin": "newpin456"})
    assert new_pin_response.status_code == 200


def test_change_user_pin_with_wrong_current_pin(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "PIN Change Fail User",
        "role": "user",
        "is_active": True,
        "pin": "correctpin"
    })
    create_response = client.post("/users/", json=payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    response = client.post("/users/change-user-pin", json={"user_id": user_id, "current_pin": "wrong-current-pin", "new_pin": "newpin456"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid current PIN"


def test_update_user(client, admin_bootstrap, admin_headers):
    create_payload = _wrapper(admin_bootstrap, {
        "display_name": "Updatable User",
        "role": "user",
        "is_active": True,
        "pin": "origpin"
    })
    create_response = client.post("/users/", json=create_payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    update_payload = {"display_name": "Updated Name"}
    response = client.put(f"/users/{user_id}", json=update_payload, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Name"


def test_delete_user(client, admin_bootstrap, admin_headers):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Deletable User",
        "role": "user",
        "is_active": True,
        "pin": "delpin"
    })
    create_response = client.post("/users/", json=payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]
    response = client.request("DELETE", f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    get_response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False
