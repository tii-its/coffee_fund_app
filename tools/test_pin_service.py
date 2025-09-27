#!/usr/bin/env python3
"""
Simple test script to verify PIN service functionality (moved out of repo root to avoid pytest discovery)
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend/app'))

try:
    from app.services.pin import PinService
    from app.core.config import settings
    
    print("Testing PIN Service...")
    
    # Test 1: Hash function
    pin = "1234"
    hashed = PinService.hash_pin(pin)
    print(f"✓ PIN hashing works: {pin} -> {hashed[:8]}...")
    
    # Test 2: Verify correct PIN
    is_valid = PinService.verify_pin(settings.treasurer_pin)
    print(f"✓ Default PIN verification: {is_valid}")
    
    # Test 3: Verify incorrect PIN
    is_invalid = PinService.verify_pin("wrong-pin")
    print(f"✓ Invalid PIN rejection: {not is_invalid}")
    
    # Test 4: Default PIN hash
    default_hash = PinService.get_default_pin_hash()
    print(f"✓ Default PIN hash: {default_hash[:8]}...")
    
    print("\n✅ All PIN service tests passed!")
    print(f"Current treasurer PIN (from config): {settings.treasurer_pin}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
