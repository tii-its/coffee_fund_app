#!/usr/bin/env python3
"""
Simple standalone test to verify PIN hashing logic
"""
import hashlib

class SimplePinService:
    """Simplified PIN service for testing"""
    
    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using SHA256"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    @staticmethod
    def verify_pin(pin: str, correct_pin: str) -> bool:
        """Verify a PIN against the correct one"""
        return SimplePinService.hash_pin(pin) == SimplePinService.hash_pin(correct_pin)

def test_pin_service():
    """Test the PIN service logic"""
    print("Testing PIN Service Logic...")
    
    # Test 1: Hash function consistency
    pin1 = "1234"
    hash1 = SimplePinService.hash_pin(pin1)
    hash2 = SimplePinService.hash_pin(pin1)
    assert hash1 == hash2, "Hash should be consistent"
    print(f"✓ Hash consistency: {pin1} -> {hash1[:8]}...")
    
    # Test 2: Different pins produce different hashes
    pin2 = "5678"
    hash3 = SimplePinService.hash_pin(pin2)
    assert hash1 != hash3, "Different pins should produce different hashes"
    print(f"✓ Hash uniqueness: {pin2} -> {hash3[:8]}...")
    
    # Test 3: PIN verification
    assert SimplePinService.verify_pin("1234", "1234"), "Correct PIN should verify"
    assert not SimplePinService.verify_pin("1234", "5678"), "Incorrect PIN should not verify"
    print("✓ PIN verification works correctly")
    
    # Test 4: Empty and edge cases
    assert SimplePinService.verify_pin("", ""), "Empty PIN should verify with empty"
    assert not SimplePinService.verify_pin("", "1234"), "Empty PIN should not verify with non-empty"
    print("✓ Edge cases handled correctly")
    
    print("\n✅ All PIN service logic tests passed!")

if __name__ == "__main__":
    test_pin_service()