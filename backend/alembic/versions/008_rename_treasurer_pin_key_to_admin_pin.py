"""Rename treasurer_pin_hash key to admin_pin_hash

Revision ID: 008
Revises: 007
Create Date: 2025-09-29 00:00:00.000000

Idempotent migration: only updates key if legacy exists and new one absent.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
author = 'auto'
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

LEGACY_KEY = 'treasurer_pin_hash'
NEW_KEY = 'admin_pin_hash'

def upgrade() -> None:
    conn = op.get_bind()
    # Check if legacy row exists
    res = conn.execute(text("SELECT id, key FROM system_settings WHERE key = :k"), {"k": LEGACY_KEY}).fetchone()
    if res:
        # Only rename if new key does not already exist
        existing_new = conn.execute(text("SELECT 1 FROM system_settings WHERE key = :k"), {"k": NEW_KEY}).fetchone()
        if not existing_new:
            conn.execute(text("UPDATE system_settings SET key = :new WHERE key = :old"), {"new": NEW_KEY, "old": LEGACY_KEY})


def downgrade() -> None:
    conn = op.get_bind()
    # Revert only if admin key exists and legacy does not (avoid clobber)
    res = conn.execute(text("SELECT id FROM system_settings WHERE key = :k"), {"k": NEW_KEY}).fetchone()
    if res:
        legacy_exists = conn.execute(text("SELECT 1 FROM system_settings WHERE key = :k"), {"k": LEGACY_KEY}).fetchone()
        if not legacy_exists:
            conn.execute(text("UPDATE system_settings SET key = :old WHERE key = :new"), {"old": LEGACY_KEY, "new": NEW_KEY})
