#!/usr/bin/env python
"""Reset or set the treasurer PIN.

Usage inside container:
  python -m app.scripts.reset_treasurer_pin            # sets to 1234 (or TREASURER_PIN env if provided)
  python -m app.scripts.reset_treasurer_pin 9876       # sets to 9876

This stores the SHA256 hash in system_settings (treasurer_pin_hash), overwriting any existing value.
"""
from app.db.session import SessionLocal
from app.models.system_settings import SystemSettings
from app.services.pin import PinService
from app.core.config import settings
import sys
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError

DEFAULT_PIN = settings.treasurer_pin or "1234"

def set_pin(pin: str):
    session = SessionLocal()
    try:
        # Quick existence check for table
        try:
            session.execute(text("SELECT 1 FROM system_settings LIMIT 1"))
        except (ProgrammingError, OperationalError) as e:
            msg = str(e)
            if 'system_settings' in msg and 'does not exist' in msg:
                print("ERROR: 'system_settings' table missing. Run 'make migrate' (after resolving duplicate Alembic revisions) and retry.")
                sys.exit(2)
            raise

        hashed = PinService.hash_pin(pin)
        row = session.query(SystemSettings).filter(SystemSettings.key == PinService.TREASURER_PIN_KEY).first()
        if row:
            row.value = hashed
            row.updated_at = datetime.utcnow()
            action = 'updated'
        else:
            row = SystemSettings(key=PinService.TREASURER_PIN_KEY, value=hashed, is_encrypted=False)
            session.add(row)
            action = 'created'
        session.commit()
        print(f"Treasurer PIN {action} and set to '{pin}'.")
    finally:
        session.close()

if __name__ == "__main__":
    pin = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PIN
    if not pin.isdigit() or len(pin) < 4:
        print("Refusing to set PIN: must be at least 4 digits.")
        sys.exit(1)
    set_pin(pin)
