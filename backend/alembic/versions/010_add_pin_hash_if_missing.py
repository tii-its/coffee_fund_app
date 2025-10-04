"""conditionally add pin_hash to users if missing

Revision ID: 010_add_pin_hash_if_missing
Revises: 009_add_admin_and_drop_email
Create Date: 2025-10-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "010_add_pin_hash_if_missing"
down_revision = "009_add_admin_and_drop_email"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "pin_hash" not in cols:
        op.add_column("users", sa.Column("pin_hash", sa.String(64), nullable=True))


def downgrade():
    # Only drop if present (symmetric safety)
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "pin_hash" in cols:
        op.drop_column("users", "pin_hash")