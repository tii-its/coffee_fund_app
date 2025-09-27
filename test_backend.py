#!/usr/bin/env python3
"""
Simple test script to verify the PIN functionality works
Run from the backend directory: python test_backend.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.pin import PinService

def test_pin_service():
    """Test the PIN service functionality"""
    print("Testing PIN Service...")
    
    # Test default PIN
    default_pin = "1234"
    print(f"Testing with default PIN: {default_pin}")
    
    # Test PIN hashing
    hashed = PinService.hash_pin(default_pin)
    print(f"Hashed PIN: {hashed[:10]}...")
    
    # Test PIN verification
    is_valid = PinService.verify_pin(default_pin)
    print(f"PIN verification result: {is_valid}")
    
    # Test wrong PIN
    wrong_pin = "5678"
    is_wrong_valid = PinService.verify_pin(wrong_pin)
    print(f"Wrong PIN verification result: {is_wrong_valid}")
    
    return is_valid and not is_wrong_valid

if __name__ == "__main__":
    try:
        success = test_pin_service()
        if success:
            print("\n✅ PIN service tests passed!")
        else:
            print("\n❌ PIN service tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)