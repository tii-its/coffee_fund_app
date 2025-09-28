"""
Test CSV export service functionality
"""
import pytest
import csv
import io
from app.models import User, Product, Consumption, MoneyMove
from app.services.csv_export import CSVExportService
from app.core.enums import UserRole, MoneyMoveType, MoneyMoveStatus
from datetime import datetime


@pytest.fixture
def db_test_user(db_session):
    user = User(
        display_name="Test User",
        email="csv.user@example.com",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def db_test_treasurer(db_session):
    treasurer = User(
        display_name="Test Treasurer",
        email="csv.treasurer@example.com",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(treasurer)
    db_session.commit()
    db_session.refresh(treasurer)
    return treasurer


@pytest.fixture
def db_test_product(db_session):
    product = Product(
        name="Coffee",
        price_cents=150,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_export_consumptions_empty(db_session):
    """Test exporting consumptions when no data exists"""
    csv_data = CSVExportService.export_consumptions(db_session, limit=1000)
    
    # Parse CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header only
    assert len(rows) == 1
    expected_headers = [
        'Date', 'User', 'Product', 'Quantity', 
        'Unit Price (€)', 'Total Amount (€)', 'Created By'
    ]
    assert rows[0] == expected_headers


def test_export_consumptions_with_data(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test exporting consumptions with data"""
    # Create consumption
    consumption = Consumption(
        user_id=db_test_user.id,
        product_id=db_test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=db_test_treasurer.id
    )
    db_session.add(consumption)
    db_session.commit()
    
    csv_data = CSVExportService.export_consumptions(db_session, limit=1000)
    
    # Parse CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header + 1 data row
    assert len(rows) == 2
    
    # Check header
    expected_headers = [
        'Date', 'User', 'Product', 'Quantity', 
        'Unit Price (€)', 'Total Amount (€)', 'Created By'
    ]
    assert rows[0] == expected_headers
    
    # Check data row
    data_row = rows[1]
    assert len(data_row) == 7
    assert data_row[1] == "Test User"        # User
    assert data_row[2] == "Coffee"           # Product
    assert data_row[3] == "2"                # Quantity
    assert data_row[4] == "1.50"             # Unit Price in euros
    assert data_row[5] == "3.00"             # Total Amount in euros
    assert data_row[6] == "Test Treasurer"   # Created By
    
    # Date should be parseable
    assert len(data_row[0]) > 0


def test_export_consumptions_multiple(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test exporting multiple consumptions"""
    # Create multiple consumptions
    consumptions_data = [
        {"qty": 1, "unit_price_cents": 150, "amount_cents": 150},
        {"qty": 3, "unit_price_cents": 200, "amount_cents": 600},
        {"qty": 2, "unit_price_cents": 100, "amount_cents": 200}
    ]
    
    for data in consumptions_data:
        consumption = Consumption(
            user_id=db_test_user.id,
            product_id=db_test_product.id,
            qty=data["qty"],
            unit_price_cents=data["unit_price_cents"],
            amount_cents=data["amount_cents"],
            created_by=db_test_treasurer.id
        )
        db_session.add(consumption)
    
    db_session.commit()
    
    csv_data = CSVExportService.export_consumptions(db_session, limit=1000)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header + 3 data rows
    assert len(rows) == 4
    
    # Check quantities are correct (should be ordered by date desc)
    quantities = [row[3] for row in rows[1:]]  # Skip header
    assert "2" in quantities
    assert "3" in quantities
    assert "1" in quantities


def test_export_consumptions_with_limit(db_session, db_test_user, db_test_product, db_test_treasurer):
    """Test exporting consumptions with limit"""
    # Create 5 consumptions
    for i in range(5):
        consumption = Consumption(
            user_id=db_test_user.id,
            product_id=db_test_product.id,
            qty=i + 1,
            unit_price_cents=150,
            amount_cents=(i + 1) * 150,
            created_by=db_test_treasurer.id
        )
        db_session.add(consumption)
    
    db_session.commit()
    
    # Export with limit of 3
    csv_data = CSVExportService.export_consumptions(db_session, limit=3)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header + 3 data rows (limited)
    assert len(rows) == 4


def test_export_money_moves_empty(db_session):
    """Test exporting money moves when no data exists"""
    csv_data = CSVExportService.export_money_moves(db_session, limit=1000)
    
    # Parse CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header only
    assert len(rows) == 1
    expected_headers = [
        'Created Date', 'Type', 'User', 'Amount (€)', 
        'Status', 'Note', 'Created By', 'Confirmed Date', 'Confirmed By'
    ]
    assert rows[0] == expected_headers


def test_export_money_moves_pending(db_session, db_test_user, db_test_treasurer):
    """Test exporting pending money move"""
    money_move = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        note="Test deposit",
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.PENDING
    )
    db_session.add(money_move)
    db_session.commit()
    
    csv_data = CSVExportService.export_money_moves(db_session, limit=1000)
    
    # Parse CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header + 1 data row
    assert len(rows) == 2
    
    # Check data row
    data_row = rows[1]
    assert len(data_row) == 9
    assert data_row[1] == "Deposit"           # Type (capitalized)
    assert data_row[2] == "Test User"         # User
    assert data_row[3] == "10.00"             # Amount in euros
    assert data_row[4] == "Pending"           # Status (capitalized)
    assert data_row[5] == "Test deposit"      # Note
    assert data_row[6] == "Test Treasurer"    # Created By
    assert data_row[7] == ""                  # Confirmed Date (empty for pending)
    assert data_row[8] == ""                  # Confirmed By (empty for pending)


def test_export_money_moves_confirmed(db_session, db_test_user, db_test_treasurer):
    """Test exporting confirmed money move"""
    # Create confirmer
    confirmer = User(
        display_name="Confirmer",
        email="csv.confirmer@example.com",
        role=UserRole.TREASURER,
        is_active=True
    )
    db_session.add(confirmer)
    db_session.commit()
    db_session.refresh(confirmer)
    
    confirmed_time = datetime.utcnow()
    money_move = MoneyMove(
        type=MoneyMoveType.PAYOUT,
        user_id=db_test_user.id,
        amount_cents=500,
        note="Test payout",
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.CONFIRMED,
        confirmed_at=confirmed_time,
        confirmed_by=confirmer.id
    )
    db_session.add(money_move)
    db_session.commit()
    
    csv_data = CSVExportService.export_money_moves(db_session, limit=1000)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 2
    data_row = rows[1]
    assert data_row[1] == "Payout"        # Type
    assert data_row[3] == "5.00"          # Amount in euros
    assert data_row[4] == "Confirmed"     # Status
    assert data_row[7] != ""              # Confirmed Date should not be empty
    assert data_row[8] == "Confirmer"     # Confirmed By


def test_export_money_moves_no_note(db_session, db_test_user, db_test_treasurer):
    """Test exporting money move without note"""
    money_move = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=db_test_user.id,
        amount_cents=1000,
        # note is None
        created_by=db_test_treasurer.id,
        status=MoneyMoveStatus.PENDING
    )
    db_session.add(money_move)
    db_session.commit()
    
    csv_data = CSVExportService.export_money_moves(db_session, limit=1000)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 2
    data_row = rows[1]
    assert data_row[5] == ""  # Note should be empty string


def test_export_user_balances_empty(db_session):
    """Test exporting user balances with empty data"""
    balances = []
    csv_data = CSVExportService.export_user_balances(db_session, balances)
    
    # Parse CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header only
    assert len(rows) == 1
    assert rows[0] == ['User', 'Balance (€)', 'Role', 'Active']


def test_export_user_balances_with_data(db_session, db_test_user, db_test_treasurer):
    """Test exporting user balances with data"""
    balances = [
        {
            'user': {
                'display_name': 'Test User',
                'role': UserRole.USER,
                'is_active': True
            },
            'balance_cents': 1500  # 15.00 euros
        },
        {
            'user': {
                'display_name': 'Test Treasurer',
                'role': UserRole.TREASURER,
                'is_active': False
            },
            'balance_cents': -250  # -2.50 euros
        }
    ]
    
    csv_data = CSVExportService.export_user_balances(db_session, balances)
    
    # Parse CSV
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header + 2 data rows
    assert len(rows) == 3
    assert rows[0] == ['User', 'Balance (€)', 'Role', 'Active']
    
    # Check first user
    user_row = rows[1]
    assert user_row[0] == "Test User"
    assert user_row[1] == "15.00"
    assert user_row[2] == "User"
    assert user_row[3] == "Yes"
    
    # Check second user
    treasurer_row = rows[2]
    assert treasurer_row[0] == "Test Treasurer"
    assert treasurer_row[1] == "-2.50"
    assert treasurer_row[2] == "Treasurer"
    assert treasurer_row[3] == "No"


def test_export_user_balances_zero_balance(db_session):
    """Test exporting user with zero balance"""
    balances = [
        {
            'user': {
                'display_name': 'Zero User',
                'role': UserRole.USER,
                'is_active': True
            },
            'balance_cents': 0
        }
    ]
    
    csv_data = CSVExportService.export_user_balances(db_session, balances)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 2
    data_row = rows[1]
    assert data_row[1] == "0.00"


def test_export_currency_formatting(db_session):
    """Test that currency values are formatted correctly"""
    balances = [
        {
            'user': {'display_name': 'User 1', 'role': UserRole.USER, 'is_active': True},
            'balance_cents': 1  # 0.01 euros
        },
        {
            'user': {'display_name': 'User 2', 'role': UserRole.USER, 'is_active': True},
            'balance_cents': 10  # 0.10 euros
        },
        {
            'user': {'display_name': 'User 3', 'role': UserRole.USER, 'is_active': True},
            'balance_cents': 100  # 1.00 euros
        },
        {
            'user': {'display_name': 'User 4', 'role': UserRole.USER, 'is_active': True},
            'balance_cents': 1234  # 12.34 euros
        }
    ]
    
    csv_data = CSVExportService.export_user_balances(db_session, balances)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 5  # header + 4 users
    
    # Check formatting
    assert rows[1][1] == "0.01"
    assert rows[2][1] == "0.10"
    assert rows[3][1] == "1.00"
    assert rows[4][1] == "12.34"


def test_csv_export_special_characters(db_session, db_test_treasurer):
    """Test CSV export handles special characters correctly"""
    # Create user with special characters
    special_user = User(
        display_name="Müller, Hans-Peter \"Test\"",
        email="csv.special@example.com",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(special_user)
    
    # Create product with special characters
    special_product = Product(
        name="Café & Tea, \"Premium\"",
        price_cents=250,
        is_active=True
    )
    db_session.add(special_product)
    db_session.commit()
    db_session.refresh(special_user)
    db_session.refresh(special_product)
    
    # Create consumption
    consumption = Consumption(
        user_id=special_user.id,
        product_id=special_product.id,
        qty=1,
        unit_price_cents=250,
        amount_cents=250,
        created_by=db_test_treasurer.id
    )
    db_session.add(consumption)
    db_session.commit()
    
    csv_data = CSVExportService.export_consumptions(db_session, limit=1000)
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 2
    data_row = rows[1]
    assert "Müller, Hans-Peter" in data_row[1]
    assert "Café & Tea" in data_row[2]