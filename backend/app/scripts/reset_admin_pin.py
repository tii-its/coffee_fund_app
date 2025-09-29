#!/usr/bin/env python
"""Reset or set the admin PIN (replaces treasurer PIN).

Usage inside container:
  python -m app.scripts.reset_admin_pin            # sets to ADMIN_PIN env (or 1234 fallback)
  python -m app.scripts.reset_admin_pin 9876       # sets to 9876

Stores SHA256 hash in system_settings (admin_pin_hash), migrating legacy key if present.
"""
from app.db.session import SessionLocal
from app.models.system_settings import SystemSettings
from app.services.pin import PinService
from app.core.config import settings
import sys
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError

default_pin = settings.admin_pin or "1234"


def set_admin_pin(pin: str):
    session = SessionLocal()
    try:
        # Validate table exists
        try:
            session.execute(text("SELECT 1 FROM system_settings LIMIT 1"))
        except (ProgrammingError, OperationalError) as e:
            msg = str(e)
            if 'system_settings' in msg and 'does not exist' in msg:
                print("ERROR: 'system_settings' table missing. Run 'make migrate' and retry.")
                sys.exit(2)
            raise

        hashed = PinService.hash_pin(pin)
        # Try new key first
        row = session.query(SystemSettings).filter(SystemSettings.key == PinService.ADMIN_PIN_KEY).first()
        if not row:
            # Check legacy key
            legacy = session.query(SystemSettings).filter(SystemSettings.key == PinService.TREASURER_PIN_KEY).first()
            if legacy:
                legacy.key = PinService.ADMIN_PIN_KEY
                row = legacy
        if row:
            row.value = hashed
            row.updated_at = datetime.utcnow()
            action = 'updated'
        else:
            row = SystemSettings(key=PinService.ADMIN_PIN_KEY, value=hashed, is_encrypted=False)
            session.add(row)
            action = 'created'
        session.commit()
        print(f"Admin PIN {action} and set to '{pin}'.")
    finally:
        session.close()


if __name__ == "__main__":
    pin = sys.argv[1] if len(sys.argv) > 1 else default_pin
    if not pin.isdigit() or len(pin) < 4:
        print("Refusing to set PIN: must be at least 4 digits.")
        sys.exit(1)
    set_admin_pin(pin)
