"""
Test QR code service functionality
"""
import pytest
import base64
import io
from app.services.qr_code import QRCodeService
import uuid

# Try to import PIL for image validation tests
PIL_AVAILABLE = True
try:
    from PIL import Image  # noqa: F401
except ImportError:
    PIL_AVAILABLE = False


def test_generate_qr_code_basic():
    """Test basic QR code generation"""
    data = "test_data_123"
    qr_code = QRCodeService.generate_qr_code(data)
    
    # Should return base64 encoded data URL
    assert qr_code.startswith("data:image/png;base64,")
    
    # Extract base64 part
    base64_part = qr_code.split(',')[1]
    
    # Should be valid base64
    try:
        decoded = base64.b64decode(base64_part)
        assert len(decoded) > 0
    except Exception as e:
        pytest.fail(f"Invalid base64 data: {e}")


def test_generate_qr_code_empty_string():
    """Test QR code generation with empty string"""
    qr_code = QRCodeService.generate_qr_code("")
    
    assert qr_code.startswith("data:image/png;base64,")
    base64_part = qr_code.split(',')[1]
    
    # Should still be valid base64
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


def test_generate_qr_code_long_string():
    """Test QR code generation with long string"""
    long_data = "a" * 1000  # Very long string
    qr_code = QRCodeService.generate_qr_code(long_data)
    
    assert qr_code.startswith("data:image/png;base64,")
    base64_part = qr_code.split(',')[1]
    
    # Should still be valid base64
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


def test_generate_qr_code_special_characters():
    """Test QR code generation with special characters"""
    special_data = "Hello 世界! @#$%^&*()_+-=[]{}|;':\",./<>?"
    qr_code = QRCodeService.generate_qr_code(special_data)
    
    assert qr_code.startswith("data:image/png;base64,")
    base64_part = qr_code.split(',')[1]
    
    # Should be valid base64
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
def test_generate_qr_code_is_valid_image():
    """Test that generated QR code is a valid PNG image"""
    data = "test_image_validation"
    qr_code = QRCodeService.generate_qr_code(data)
    
    # Extract base64 part and decode
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    
    # Should be able to open as image
    try:
        image = Image.open(io.BytesIO(decoded))
        
        # Check basic image properties
        assert image.format == "PNG"
        assert image.mode in ["1", "L", "RGB", "RGBA"]  # Valid PIL modes for QR codes
        assert image.size[0] > 0
        assert image.size[1] > 0
        
        # QR codes are typically square
        assert image.size[0] == image.size[1]
        
    except Exception as e:
        pytest.fail(f"Generated QR code is not a valid image: {e}")


def test_generate_user_qr_code():
    """Test generating QR code for user ID"""
    user_id = str(uuid.uuid4())
    qr_code = QRCodeService.generate_user_qr_code(user_id)
    
    assert qr_code.startswith("data:image/png;base64,")
    base64_part = qr_code.split(',')[1]
    
    # Should be valid base64
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


def test_generate_user_qr_code_different_uuids():
    """Test that different user IDs generate different QR codes"""
    user_id1 = str(uuid.uuid4())
    user_id2 = str(uuid.uuid4())
    
    qr_code1 = QRCodeService.generate_user_qr_code(user_id1)
    qr_code2 = QRCodeService.generate_user_qr_code(user_id2)
    
    # Should be different
    assert qr_code1 != qr_code2


def test_generate_qr_code_consistency():
    """Test that same input generates same QR code"""
    data = "consistent_test_data"
    
    qr_code1 = QRCodeService.generate_qr_code(data)
    qr_code2 = QRCodeService.generate_qr_code(data)
    
    # Should generate identical QR codes for same input
    assert qr_code1 == qr_code2


def test_generate_qr_code_url_format():
    """Test URL data in QR code"""
    url = "https://example.com/user/12345"
    qr_code = QRCodeService.generate_qr_code(url)
    
    assert qr_code.startswith("data:image/png;base64,")
    
    # Should be valid image
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    image = Image.open(io.BytesIO(decoded))
    assert image.format == "PNG"


def test_generate_qr_code_json_data():
    """Test JSON data in QR code"""
    json_data = '{"user_id": "123", "name": "Test User", "role": "user"}'
    qr_code = QRCodeService.generate_qr_code(json_data)
    
    assert qr_code.startswith("data:image/png;base64,")
    
    # Should be valid
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


def test_generate_qr_code_numeric_data():
    """Test numeric data in QR code"""
    numeric_data = "1234567890"
    qr_code = QRCodeService.generate_qr_code(numeric_data)
    
    assert qr_code.startswith("data:image/png;base64,")
    
    # Should be valid
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
def test_qr_code_size_reasonable():
    """Test that QR code has reasonable size"""
    data = "reasonable_size_test"
    qr_code = QRCodeService.generate_qr_code(data)
    
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    image = Image.open(io.BytesIO(decoded))
    
    # Check size is reasonable (not too small, not too large)
    width, height = image.size
    assert 50 <= width <= 1000  # Reasonable range
    assert 50 <= height <= 1000
    
    # Should be square
    assert width == height


def test_qr_code_different_inputs_different_outputs():
    """Test that different inputs produce different QR codes"""
    inputs = ["data1", "data2", "data3", "completely different string"]
    qr_codes = []
    
    for data in inputs:
        qr_code = QRCodeService.generate_qr_code(data)
        qr_codes.append(qr_code)
    
    # All should be different
    for i, qr_code1 in enumerate(qr_codes):
        for j, qr_code2 in enumerate(qr_codes):
            if i != j:
                assert qr_code1 != qr_code2


@pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
def test_qr_code_error_correction():
    """Test QR code with error correction (implicit test through successful generation)"""
    # The QR code service should use error correction
    # This is tested implicitly by generating codes and verifying they're valid
    test_data = "error_correction_test_data_with_some_length"
    qr_code = QRCodeService.generate_qr_code(test_data)
    
    assert qr_code.startswith("data:image/png;base64,")
    
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    image = Image.open(io.BytesIO(decoded))
    
    # Should be a valid QR code image
    assert image.format == "PNG"
    assert image.size[0] > 0
    assert image.size[1] > 0


# Edge cases and error conditions
def test_qr_code_whitespace_handling():
    """Test QR code generation with whitespace"""
    data_with_spaces = "  test data with spaces  "
    qr_code = QRCodeService.generate_qr_code(data_with_spaces)
    
    assert qr_code.startswith("data:image/png;base64,")
    
    # Should preserve whitespace (different from trimmed version)
    trimmed_data = data_with_spaces.strip()
    qr_code_trimmed = QRCodeService.generate_qr_code(trimmed_data)
    
    assert qr_code != qr_code_trimmed


def test_qr_code_newline_handling():
    """Test QR code generation with newlines"""
    data_with_newlines = "line1\\nline2\\nline3"
    qr_code = QRCodeService.generate_qr_code(data_with_newlines)
    
    assert qr_code.startswith("data:image/png;base64,")
    base64_part = qr_code.split(',')[1]
    decoded = base64.b64decode(base64_part)
    assert len(decoded) > 0


def test_user_qr_code_specific_format():
    """Test that user QR codes work with UUID format"""
    # Test with actual UUID format
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    qr_code = QRCodeService.generate_user_qr_code(user_id)
    
    assert qr_code.startswith("data:image/png;base64,")
    
    # Should be different from other UUID
    user_id2 = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    qr_code2 = QRCodeService.generate_user_qr_code(user_id2)
    
    assert qr_code != qr_code2