"""
Test export API endpoints
"""
import pytest
import csv
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db, Base
from uuid import uuid4

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_exports.db"

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
def test_treasurer(client):
    """Create a test treasurer"""
    user_data = {
        "display_name": "Test Treasurer", 
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    return response.json()


@pytest.fixture
def test_product(client):
    """Create a test product"""
    product_data = {
        "name": "Coffee",
        "price_cents": 150,
        "is_active": True
    }
    response = client.post("/products/", json=product_data)
    return response.json()


@pytest.fixture
def sample_consumption(client, test_user, test_product, test_treasurer):
    """Create a sample consumption"""
    consumption_data = {
        "user_id": test_user["id"],
        "product_id": test_product["id"],
        "qty": 2
    }
    response = client.post(
        f"/consumptions/?creator_id={test_treasurer['id']}", 
        json=consumption_data
    )
    return response.json()


@pytest.fixture
def sample_money_move(client, test_user, test_treasurer):
    """Create a sample money move"""
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test deposit"
    }
    response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=money_move_data
    )
    return response.json()


def test_export_consumptions_empty(client):
    """Test exporting consumptions when no data exists"""
    response = client.get("/exports/consumptions")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=consumptions.csv" in response.headers.get("content-disposition", "")
    
    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header row only
    assert len(rows) == 1
    assert rows[0] == ['Date', 'User', 'Product', 'Quantity', 'Unit Price (€)', 'Total Amount (€)', 'Created By']


def test_export_consumptions_with_data(client, sample_consumption):
    """Test exporting consumptions with data"""
    response = client.get("/exports/consumptions")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header + 1 data row
    assert len(rows) == 2
    assert rows[0] == ['Date', 'User', 'Product', 'Quantity', 'Unit Price (€)', 'Total Amount (€)', 'Created By']
    
    # Check data row
    data_row = rows[1]
    assert len(data_row) == 7
    assert data_row[1] == "Test User"  # User name
    assert data_row[2] == "Coffee"     # Product name
    assert data_row[3] == "2"          # Quantity
    assert data_row[4] == "1.50"       # Unit price in euros
    assert data_row[5] == "3.00"       # Total amount in euros
    assert data_row[6] == "Test Treasurer"  # Creator name


def test_export_consumptions_with_limit(client, test_user, test_product, test_treasurer):
    """Test exporting consumptions with limit parameter"""
    # Create multiple consumptions
    for i in range(5):
        consumption_data = {
            "user_id": test_user["id"],
            "product_id": test_product["id"],
            "qty": i + 1
        }
        client.post(
            f"/consumptions/?creator_id={test_treasurer['id']}", 
            json=consumption_data
        )
    
    response = client.get("/exports/consumptions?limit=3")
    assert response.status_code == 200
    
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header + 3 data rows (limited)
    assert len(rows) == 4  # 1 header + 3 data rows


def test_export_money_moves_empty(client):
    """Test exporting money moves when no data exists"""
    response = client.get("/exports/money-moves")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=money_moves.csv" in response.headers.get("content-disposition", "")
    
    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header row only
    assert len(rows) == 1
    expected_headers = [
        'Created Date', 'Type', 'User', 'Amount (€)', 
        'Status', 'Note', 'Created By', 'Confirmed Date', 'Confirmed By'
    ]
    assert rows[0] == expected_headers


def test_export_money_moves_with_data(client, sample_money_move):
    """Test exporting money moves with data"""
    response = client.get("/exports/money-moves")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header + 1 data row
    assert len(rows) == 2
    
    # Check data row
    data_row = rows[1]
    assert len(data_row) == 9
    assert data_row[1] == "Deposit"        # Type
    assert data_row[2] == "Test User"      # User name
    assert data_row[3] == "10.00"          # Amount in euros
    assert data_row[4] == "Pending"        # Status
    assert data_row[5] == "Test deposit"   # Note
    assert data_row[6] == "Test Treasurer" # Creator name
    assert data_row[7] == ""               # Confirmed date (empty for pending)
    assert data_row[8] == ""               # Confirmed by (empty for pending)


def test_export_money_moves_confirmed(client, test_user, test_treasurer, test_treasurer2):
    """Test exporting confirmed money move"""
    # Create money move
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test deposit"
    }
    create_response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    # Confirm it
    client.patch(f"/money-moves/{money_move_id}/confirm?confirmer_id={test_treasurer2['id']}")
    
    response = client.get("/exports/money-moves")
    assert response.status_code == 200
    
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    assert len(rows) == 2
    data_row = rows[1]
    assert data_row[4] == "Confirmed"           # Status
    assert data_row[7] != ""                    # Confirmed date should not be empty
    assert data_row[8] == "Test Treasurer 2"   # Confirmed by


@pytest.fixture
def test_treasurer2(client):
    """Create a second test treasurer"""
    user_data = {
        "display_name": "Test Treasurer 2", 
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    return response.json()


def test_export_balances_empty(client):
    """Test exporting balances when no users exist"""
    response = client.get("/exports/balances")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=balances.csv" in response.headers.get("content-disposition", "")
    
    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header row only
    assert len(rows) == 1
    assert rows[0] == ['User', 'Balance (€)', 'Role', 'Active']


def test_export_balances_with_users(client, test_user, test_treasurer):
    """Test exporting balances with users"""
    response = client.get("/exports/balances")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    # Parse CSV content
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Should have header + 2 data rows (2 users)
    assert len(rows) == 3
    assert rows[0] == ['User', 'Balance (€)', 'Role', 'Active']
    
    # Check that we have both users in the export
    user_names = [row[0] for row in rows[1:]]
    assert "Test User" in user_names
    assert "Test Treasurer" in user_names
    
    # Check balance format and other fields
    for row in rows[1:]:
        assert len(row) == 4
        # Balance should be in format like "0.00"
        assert "." in row[1]
        # Role should be capitalized
        assert row[2] in ["User", "Treasurer"]
        # Active should be Yes/No
        assert row[3] in ["Yes", "No"]


def test_export_balances_with_transactions(client, test_user, test_treasurer, test_treasurer2):
    """Test exporting balances with actual balance data"""
    # Create a confirmed deposit
    money_move_data = {
        "type": "deposit",
        "user_id": test_user["id"],
        "amount_cents": 1000,
        "note": "Test deposit"
    }
    create_response = client.post(
        f"/money-moves/?creator_id={test_treasurer['id']}", 
        json=money_move_data
    )
    money_move_id = create_response.json()["id"]
    
    # Confirm the deposit
    client.patch(f"/money-moves/{money_move_id}/confirm?confirmer_id={test_treasurer2['id']}")
    
    response = client.get("/exports/balances")
    assert response.status_code == 200
    
    csv_content = response.text
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    # Find the test user's row
    test_user_row = None
    for row in rows[1:]:
        if row[0] == "Test User":
            test_user_row = row
            break
    
    assert test_user_row is not None
    assert test_user_row[1] == "10.00"  # Balance should be 10.00 euros