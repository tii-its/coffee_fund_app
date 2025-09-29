"""Add pin_hash field to users table

Revision ID: 009
Revises: 008
Create Date: 2025-01-14 10:00:00.000000

Add mandatory pin_hash field for user PIN authentication.
All existing users get a default PIN hash that needs to be changed.
"""
from alembic import op
import sqlalchemy as sa
import hashlib

# revision identifiers
author = 'auto'
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None

def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA256"""
    return hashlib.sha256(pin.encode()).hexdigest()

def upgrade() -> None:
    # Add pin_hash column as nullable first
    op.add_column('users', sa.Column('pin_hash', sa.String(64), nullable=True))
    
    # Set default PIN hash for all existing users (they will need to change this)
    default_pin_hash = hash_pin("0000")  # Default PIN: 0000
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE users SET pin_hash = :pin_hash WHERE pin_hash IS NULL"), 
                 {"pin_hash": default_pin_hash})
    
    # Make column non-nullable
    op.alter_column('users', 'pin_hash', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'pin_hash')