"""Debug test to understand fixture issues"""
import pytest

def test_debug_fixture_behavior(client, test_user, test_product, test_treasurer):
    """Debug test to see what's in the fixtures"""
    print(f"\ntest_user type: {type(test_user)}")
    print(f"test_user: {test_user}")
    print(f"test_user has 'id': {'id' in test_user if isinstance(test_user, dict) else False}")
    
    print(f"\ntest_product type: {type(test_product)}")
    print(f"test_product: {test_product}")
    print(f"test_product has 'id': {'id' in test_product if isinstance(test_product, dict) else False}")
    
    print(f"\ntest_treasurer type: {type(test_treasurer)}")
    print(f"test_treasurer: {test_treasurer}")
    print(f"test_treasurer has 'id': {'id' in test_treasurer if isinstance(test_treasurer, dict) else False}")
    
    # Try using them
    if isinstance(test_user, dict) and 'id' in test_user:
        print(f"\nUser ID: {test_user['id']}")
    else:
        print("\ntest_user does not have 'id' key!")
        if hasattr(test_user, 'keys'):
            print(f"test_user keys: {list(test_user.keys())}")

@pytest.fixture
def test_user(client):
    """Create a test user"""
    user_data = {
        "display_name": "Test User",
        "role": "user",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    print(f"User creation response: {response.status_code}")
    if response.status_code != 200:
        print(f"User creation failed: {response.text}")
    result = response.json()
    print(f"User creation result: {result}")
    return result

@pytest.fixture
def test_treasurer(client):
    """Create a test treasurer"""
    user_data = {
        "display_name": "Test Treasurer", 
        "role": "treasurer",
        "is_active": True
    }
    response = client.post("/users/", json=user_data)
    print(f"Treasurer creation response: {response.status_code}")
    if response.status_code != 200:
        print(f"Treasurer creation failed: {response.text}")
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
    print(f"Product creation response: {response.status_code}")
    if response.status_code != 200:
        print(f"Product creation failed: {response.text}")
    return response.json()