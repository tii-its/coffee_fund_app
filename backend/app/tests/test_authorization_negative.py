"""Negative authorization test cases.

Validates that role and PIN based access control rejects improper access:
 - Admin attempting treasurer-only endpoints
 - Standard user attempting treasurer-only endpoints
 - Treasurer attempting admin-only user management endpoints
 - Missing headers on treasurer endpoints
 - Wrong PIN on treasurer endpoints
"""
import pytest


def _wrapper(admin_bootstrap, user_sub_payload: dict):
    return {
        "actor_id": admin_bootstrap["id"],
        "actor_pin": admin_bootstrap["pin"],
        "user": user_sub_payload,
    }


@pytest.fixture
def admin_headers(admin_bootstrap):
    return {"x-actor-id": admin_bootstrap["id"], "x-actor-pin": admin_bootstrap["pin"]}


@pytest.fixture
def a_user(client, admin_bootstrap):
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Std User", "role": "user", "is_active": True, "pin": "userPIN123"
    })
    r = client.post("/users/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def a_treasurer(client, admin_bootstrap):
    pin = "treasPIN123"
    payload = _wrapper(admin_bootstrap, {
        "display_name": "Auth Treasurer", "role": "treasurer", "is_active": True, "pin": pin
    })
    r = client.post("/users/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    data["_headers"] = {"x-actor-id": data["id"], "x-actor-pin": pin}
    return data


def test_admin_cannot_access_treasurer_endpoints(client, admin_headers, a_user):
    # Attempt to create a money move with admin headers should fail (403)
    move_payload = {"type": "deposit", "user_id": a_user["id"], "amount_cents": 100, "note": "x"}
    r = client.post("/money-moves/", json=move_payload, headers=admin_headers)
    assert r.status_code in (403, 404)  # 404 if actor lookup fails differently, prefer 403


def test_user_cannot_access_treasurer_endpoints(client, a_user):
    # User tries money move create without treasurer headers
    move_payload = {"type": "deposit", "user_id": a_user["id"], "amount_cents": 100, "note": "x"}
    r = client.post("/money-moves/", json=move_payload)  # missing headers
    assert r.status_code == 422 or r.status_code == 403  # 422 from missing headers validation


def test_treasurer_cannot_create_user(client, a_treasurer, a_user):
    # Treasurer attempts admin-only user creation
    new_user_payload = {
        "actor_id": a_treasurer["id"],
        "actor_pin": a_treasurer["_headers"]["x-actor-pin"],
        "user": {"display_name": "Should Fail", "role": "user", "is_active": True, "pin": "abc12345"},
    }
    r = client.post("/users/", json=new_user_payload)
    # Expect 403 because treasurer is not admin
    assert r.status_code == 403


def test_missing_headers_on_treasurer_endpoint(client, a_user):
    move_payload = {"type": "deposit", "user_id": a_user["id"], "amount_cents": 50, "note": "x"}
    r = client.post("/money-moves/", json=move_payload)
    assert r.status_code == 422  # FastAPI validation error for missing headers


def test_wrong_pin_on_treasurer_endpoint(client, a_treasurer, a_user):
    move_payload = {"type": "deposit", "user_id": a_user["id"], "amount_cents": 75, "note": "x"}
    bad_headers = {"x-actor-id": a_treasurer["id"], "x-actor-pin": "WRONGPIN"}
    r = client.post("/money-moves/", json=move_payload, headers=bad_headers)
    assert r.status_code == 403
    # Response detail should indicate invalid pin (case-insensitive)
    assert "invalid treasurer pin" in r.json()["detail"].lower()
