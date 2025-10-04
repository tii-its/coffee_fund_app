"""
Integration tests for complete business workflows
"""
import pytest
import uuid


def _wrapper(admin_bootstrap, user_sub_payload: dict):
    return {"actor_id": admin_bootstrap["id"], "actor_pin": admin_bootstrap["pin"], "user": user_sub_payload}


@pytest.fixture
def setup_users_and_product(client, admin_bootstrap):
    import time
    ts = int(time.time()*1000)
    user = client.post("/users/", json=_wrapper(admin_bootstrap, {"display_name": "Coffee Consumer", "role": "user", "is_active": True, "pin": "testpin123"})).json()
    t1_pin = "treasOnePIN"; t2_pin = "treasTwoPIN"
    treasurer1 = client.post("/users/", json=_wrapper(admin_bootstrap, {"display_name": "Treasurer One", "role": "treasurer", "is_active": True, "pin": t1_pin})).json()
    treasurer2 = client.post("/users/", json=_wrapper(admin_bootstrap, {"display_name": "Treasurer Two", "role": "treasurer", "is_active": True, "pin": t2_pin})).json()
    treasurer1["_headers"] = {"x-actor-id": treasurer1["id"], "x-actor-pin": t1_pin}
    treasurer2["_headers"] = {"x-actor-id": treasurer2["id"], "x-actor-pin": t2_pin}
    product = client.post("/products/", json={"name": f"Premium Coffee {ts}", "price_cents": 200, "is_active": True}, headers=treasurer1["_headers"]).json()
    return {"user": user, "treasurer1": treasurer1, "treasurer2": treasurer2, "product": product}
def test_deposit_rejection_workflow(client, setup_users_and_product):
    """Test deposit rejection workflow"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    
    # Create deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,
        "note": "Test deposit for rejection"
    }
    
    create_response = client.post("/money-moves/", json=deposit_data, headers=treasurer1["_headers"])
    money_move = create_response.json()
    
    # Reject the deposit
    reject_response = client.patch(f"/money-moves/{money_move['id']}/reject", headers=treasurer2["_headers"])
    assert reject_response.status_code == 200
    rejected_move = reject_response.json()
    
    assert rejected_move["status"] == "rejected"
    assert rejected_move["confirmed_by"] == treasurer2["id"]
    
    # Balance should still be 0
    balance_after_reject_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_reject_resp.status_code == 200
    assert balance_after_reject_resp.json()["balance_cents"] == 0


def test_consumption_workflow(client, setup_users_and_product):
    """Test consumption workflow: deposit -> consume -> check balance"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Step 1: Add money to user account
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,  # 10 euros
        "note": "Initial deposit"
    }
    
    create_response = client.post("/money-moves/", json=deposit_data, headers=treasurer1["_headers"])
    money_move = create_response.json()
    
    # Confirm deposit
    client.patch(f"/money-moves/{money_move['id']}/confirm", headers=treasurer2["_headers"])
    
    # Verify balance
    balance_after_deposit_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_deposit_resp.status_code == 200
    assert balance_after_deposit_resp.json()["balance_cents"] == 1000
    
    # Step 2: User consumes coffee
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 3  # 3 coffees at 200 cents each = 600 cents
    }
    
    consume_response = client.post("/consumptions/", json=consumption_data, headers=treasurer1["_headers"])
    assert consume_response.status_code == 201
    consumption = consume_response.json()
    
    # Verify consumption details
    assert consumption["qty"] == 3
    assert consumption["unit_price_cents"] == 200  # Product price
    assert consumption["amount_cents"] == 600  # 3 * 200
    
    # Step 3: Check updated balance
    balance_after_consumption_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_consumption_resp.status_code == 200
    assert balance_after_consumption_resp.json()["balance_cents"] == 400
    
    # Step 4: Check consumption history
    user_consumptions_response = client.get(f"/consumptions/user/{user['id']}/recent")
    assert user_consumptions_response.status_code == 200
    user_consumptions = user_consumptions_response.json()
    
    assert len(user_consumptions) == 1
    assert user_consumptions[0]["id"] == consumption["id"]


def test_multiple_consumptions_and_balance_tracking(client, setup_users_and_product):
    """Test multiple consumptions and accurate balance tracking"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Add initial money
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 2000,  # 20 euros
        "note": "Large deposit"
    }
    
    create_response = client.post("/money-moves/", json=deposit_data, headers=treasurer1["_headers"])
    client.patch(
        f"/money-moves/{create_response.json()['id']}/confirm",
        headers=treasurer2["_headers"],
    )
    
    # Multiple consumption sessions
    consumption_sessions = [
        {"qty": 2, "expected_cost": 400},  # 2 * 200
        {"qty": 1, "expected_cost": 200},  # 1 * 200
        {"qty": 3, "expected_cost": 600},  # 3 * 200
    ]
    
    total_spent = 0
    
    for i, session in enumerate(consumption_sessions):
        consumption_data = {
            "user_id": user["id"],
            "product_id": product["id"],
            "qty": session["qty"]
        }
        
        response = client.post(
            "/consumptions/",
            json=consumption_data,
            headers=treasurer1["_headers"],
        )
        assert response.status_code == 201
        
        consumption = response.json()
        assert consumption["amount_cents"] == session["expected_cost"]
        
        total_spent += session["expected_cost"]
        
        # Check balance after each consumption
        balance_iter_resp = client.get(f"/users/{user['id']}/balance")
        assert balance_iter_resp.status_code == 200
        expected_balance = 2000 - total_spent
        assert balance_iter_resp.json()["balance_cents"] == expected_balance
    
    # Final verification
    assert total_spent == 1200  # Total: 400 + 200 + 600
    
    final_balance_resp = client.get(f"/users/{user['id']}/balance")
    assert final_balance_resp.status_code == 200
    assert final_balance_resp.json()["balance_cents"] == 800
    
    # Check consumption history
    all_consumptions_response = client.get(f"/consumptions/?user_id={user['id']}")
    all_consumptions = all_consumptions_response.json()
    assert len(all_consumptions) == 3


def test_payout_workflow(client, setup_users_and_product):
    """Test payout workflow: deposit -> consume -> payout remaining balance"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Initial deposit
    deposit_data = {
        "type": "deposit", 
        "user_id": user["id"],
        "amount_cents": 1500,
        "note": "Test deposit for payout"
    }
    create_response = client.post(
        "/money-moves/",
        json=deposit_data,
        headers=treasurer1["_headers"],
    )
    client.patch(
        f"/money-moves/{create_response.json()['id']}/confirm",
        headers=treasurer2["_headers"],
    )
    
    # Consume some coffee
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 2  # 400 cents
    }
    client.post(
        "/consumptions/",
        json=consumption_data,
        headers=treasurer1["_headers"],
    )
    
    # Balance should be 1100 cents now
    balance_before_payout_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_before_payout_resp.status_code == 200
    assert balance_before_payout_resp.json()["balance_cents"] == 1100
    
    # Request payout
    payout_data = {
        "type": "payout",
        "user_id": user["id"],
        "amount_cents": 500,  # 5 euros payout
        "note": "Partial payout"
    }
    
    payout_response = client.post(
        "/money-moves/",
        json=payout_data,
        headers=treasurer1["_headers"],
    )
    payout_move = payout_response.json()
    
    # Balance shouldn't change yet (pending)
    balance_after_request_resp = client.get(f"/users/{user['id']}/balance")
    assert balance_after_request_resp.status_code == 200
    assert balance_after_request_resp.json()["balance_cents"] == 1100
    
    # Confirm payout
    confirm_response = client.patch(
        f"/money-moves/{payout_move['id']}/confirm",
        headers=treasurer2["_headers"],
    )
    assert confirm_response.status_code == 200
    
    # Balance should now be reduced
    final_balance_resp = client.get(f"/users/{user['id']}/balance")
    assert final_balance_resp.status_code == 200
    assert final_balance_resp.json()["balance_cents"] == 600


def test_self_confirmation_prevention(client, setup_users_and_product):
    """Test that users cannot confirm their own money moves"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    
    # Create deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,
        "note": "Self-confirmation test"
    }
    
    create_response = client.post(
        "/money-moves/",
        json=deposit_data,
        headers=treasurer1["_headers"],
    )
    money_move = create_response.json()
    
    # Try to confirm with same treasurer
    confirm_response = client.patch(
        f"/money-moves/{money_move['id']}/confirm",
        headers=treasurer1["_headers"],
    )
    
    assert confirm_response.status_code == 400
    assert "Cannot confirm own money move" in confirm_response.json()["detail"]
    
    # Verify it's still pending
    get_response = client.get(f"/money-moves/{money_move['id']}")
    move_data = get_response.json()
    assert move_data["status"] == "pending"


def test_export_integration_with_real_data(client, setup_users_and_product):
    """Test CSV export with actual transaction data"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Create transactions
    # 1. Deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 2000,
        "note": "Export test deposit"
    }
    create_response = client.post(
        "/money-moves/",
        json=deposit_data,
        headers=treasurer1["_headers"],
    )
    money_move_id = create_response.json()["id"]
    client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=treasurer2["_headers"],
    )
    
    # 2. Consumption
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 2
    }
    client.post(
        "/consumptions/",
        json=consumption_data,
        headers=treasurer1["_headers"],
    )
    
    # Test exports
    # Export consumptions
    consumptions_export = client.get("/exports/consumptions")
    assert consumptions_export.status_code == 200
    assert "text/csv" in consumptions_export.headers["content-type"]
    csv_content = consumptions_export.text
    assert "Coffee Consumer" in csv_content
    assert "Premium Coffee" in csv_content
    
    # Export money moves
    money_moves_export = client.get("/exports/money-moves")
    assert money_moves_export.status_code == 200
    assert "text/csv" in money_moves_export.headers["content-type"]
    csv_content = money_moves_export.text
    assert "Coffee Consumer" in csv_content
    assert "Export test deposit" in csv_content
    assert "Confirmed" in csv_content
    
    # Export balances
    balances_export = client.get("/exports/balances")
    assert balances_export.status_code == 200
    assert "text/csv" in balances_export.headers["content-type"]
    csv_content = balances_export.text
    assert "Coffee Consumer" in csv_content
    # Balance should be 1600 cents = 16.00 euros (2000 - 400)
    assert "16.00" in csv_content


def test_audit_trail_comprehensive(client, setup_users_and_product):
    """Test that all actions create proper audit trails"""
    data = setup_users_and_product
    user = data["user"]
    treasurer1 = data["treasurer1"]
    treasurer2 = data["treasurer2"]
    product = data["product"]
    
    # Perform various actions
    # 1. Create deposit
    deposit_data = {
        "type": "deposit",
        "user_id": user["id"],
        "amount_cents": 1000,
        "note": "Audit test deposit"
    }
    create_response = client.post(
        "/money-moves/",
        json=deposit_data,
        headers=treasurer1["_headers"],
    )
    money_move_id = create_response.json()["id"]
    
    # 2. Confirm deposit
    client.patch(
        f"/money-moves/{money_move_id}/confirm",
        headers=treasurer2["_headers"],
    )
    
    # 3. Create consumption
    consumption_data = {
        "user_id": user["id"],
        "product_id": product["id"],
        "qty": 1
    }
    client.post(
        "/consumptions/",
        json=consumption_data,
        headers=treasurer1["_headers"],
    )
    
    # Check audit entries
    audit_response = client.get("/audit/")
    assert audit_response.status_code == 200
    audit_entries = audit_response.json()
    
    # Should have multiple entries
    assert len(audit_entries) >= 3
    
    # Check for different types of actions
    actions = [entry["action"] for entry in audit_entries]
    entities = [entry["entity"] for entry in audit_entries]
    
    assert "create" in actions
    assert "confirm" in actions
    assert "money_move" in entities
    assert "consumption" in entities
    
    # Check specific audit entries
    money_move_creation = next((entry for entry in audit_entries 
                               if entry["action"] == "create" and entry["entity"] == "money_move"), None)
    assert money_move_creation is not None
    assert money_move_creation["actor_id"] == treasurer1["id"]
    
    money_move_confirmation = next((entry for entry in audit_entries 
                                  if entry["action"] == "confirm" and entry["entity"] == "money_move"), None)
    assert money_move_confirmation is not None
    assert money_move_confirmation["actor_id"] == treasurer2["id"]
    
    consumption_creation = next((entry for entry in audit_entries 
                               if entry["action"] == "create" and entry["entity"] == "consumption"), None)
    assert consumption_creation is not None
    assert consumption_creation["actor_id"] == treasurer1["id"]