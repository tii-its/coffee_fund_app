"""Add stock_purchases table

Revision ID: 006
Revises: 005
Create Date: 2025-09-27 20:15:00.000000

NOTE: Renumbered from 004 to 006 during duplicate revision normalization (originally conflicted after merge).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create stock_purchases if it does not already exist (idempotent)."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'stock_purchases' in inspector.get_table_names():
        # Table already exists from an earlier conflicting migration; skip.
        return
    op.create_table(
        'stock_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('item_name', sa.String(255), nullable=False),
        sa.Column('supplier', sa.String(255), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price_cents', sa.Integer, nullable=False),
        sa.Column('total_amount_cents', sa.Integer, nullable=False),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('receipt_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_cash_out_processed', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'stock_purchases' in inspector.get_table_names():
        op.drop_table('stock_purchases')
