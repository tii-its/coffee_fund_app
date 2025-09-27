"""Normalize existing user emails (replace spaces, lowercase)

Revision ID: 003
Revises: 002
Create Date: 2025-09-27 20:05:00.000000
"""
from alembic import op

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Replace spaces before '@' with underscores and lowercase everything
    # Only adjust rows where email contains a space to avoid unnecessary updates
    op.execute("UPDATE users SET email = regexp_replace(lower(email), ' ', '_', 'g') WHERE email LIKE '% %'")
    # Optionally could reassert uniqueness; unique constraint already exists.


def downgrade() -> None:
    # Irreversible normalization (no-op)
    pass
