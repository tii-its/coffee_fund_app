"""add pin_hash to users

Revision ID: 008
Revises: 007
Create Date: 2024-12-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pin_hash column to users table
    op.add_column('users', sa.Column('pin_hash', sa.String(64), nullable=True))


def downgrade() -> None:
    # Drop pin_hash column from users table
    op.drop_column('users', 'pin_hash')