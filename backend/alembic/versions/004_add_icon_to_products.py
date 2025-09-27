"""add_icon_to_products

Revision ID: 004
Revises: 003_normalize_emails
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add icon field to products table"""
    op.add_column('products', sa.Column('icon', sa.String(10), nullable=True, server_default='☕'))


def downgrade() -> None:
    """Remove icon field from products table"""
    op.drop_column('products', 'icon')