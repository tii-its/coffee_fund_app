import qrcode
from io import BytesIO
import base64
from typing import Optional


class QRCodeService:
    @staticmethod
    def generate_qr_code(data: str) -> str:
        """Generate QR code and return as base64 encoded string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def generate_user_qr_code(user_id: str) -> str:
        """Generate QR code for user ID"""
        return QRCodeService.generate_qr_code(user_id)