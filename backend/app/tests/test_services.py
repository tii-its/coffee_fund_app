import pytest
from app.models import User, Product, Consumption, MoneyMove
from app.services.balance import BalanceService
from app.core.enums import UserRole, MoneyMoveType, MoneyMoveStatus


@pytest.fixture
def test_user(db_session):
    user = User(
        display_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_product(db_session):
    product = Product(
        name="Coffee",
        price_cents=150,
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_balance_calculation_no_transactions(db_session, test_user):
    """Test balance calculation with no transactions"""
    balance = BalanceService.get_user_balance(db_session, str(test_user.id))
    assert balance == 0


def test_balance_calculation_with_deposit(db_session, test_user):
    """Test balance calculation with confirmed deposit"""
    # Create a confirmed deposit
    deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=test_user.id,
        amount_cents=1000,
        created_by=test_user.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    db_session.add(deposit)
    db_session.commit()
    
    balance = BalanceService.get_user_balance(db_session, str(test_user.id))
    assert balance == 1000


def test_balance_calculation_with_consumption(db_session, test_user, test_product):
    """Test balance calculation with consumption"""
    # Create a confirmed deposit first
    deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=test_user.id,
        amount_cents=1000,
        created_by=test_user.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    db_session.add(deposit)
    db_session.commit()
    
    # Create a consumption
    consumption = Consumption(
        user_id=test_user.id,
        product_id=test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=test_user.id
    )
    db_session.add(consumption)
    db_session.commit()
    
    # Balance should be deposit minus consumption (1000 - 300 = 700)
    balance = BalanceService.get_user_balance(db_session, str(test_user.id))
    assert balance == 700


def test_balance_calculation_pending_deposit_ignored(db_session, test_user, test_product):
    """Test that pending deposits are ignored in balance calculation"""
    # Create a confirmed deposit first
    confirmed_deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=test_user.id,
        amount_cents=1000,
        created_by=test_user.id,
        status=MoneyMoveStatus.CONFIRMED
    )
    db_session.add(confirmed_deposit)
    
    # Create a consumption
    consumption = Consumption(
        user_id=test_user.id,
        product_id=test_product.id,
        qty=2,
        unit_price_cents=150,
        amount_cents=300,
        created_by=test_user.id
    )
    db_session.add(consumption)
    
    # Create a pending deposit
    pending_deposit = MoneyMove(
        type=MoneyMoveType.DEPOSIT,
        user_id=test_user.id,
        amount_cents=500,
        created_by=test_user.id,
        status=MoneyMoveStatus.PENDING
    )
    db_session.add(pending_deposit)
    db_session.commit()
    
    # Balance should be confirmed deposit minus consumption = 700 (pending deposits don't count)
    balance = BalanceService.get_user_balance(db_session, str(test_user.id))
    assert balance == 700