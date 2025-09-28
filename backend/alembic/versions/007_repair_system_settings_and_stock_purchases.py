"""Repair system_settings and stock_purchases presence

Revision ID: 007
Revises: 006
Create Date: 2025-09-28 00:00:00.000000

Ensures tables added despite earlier duplicate revision conflicts. Safe/idempotent.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect, text

# revision identifiers
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # system_settings table
    if 'system_settings' not in tables:
        op.create_table(
            'system_settings',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('key', sa.String(), nullable=False),
            sa.Column('value', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_encrypted', sa.Boolean, server_default=sa.text('false'), nullable=False),
        )
        op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=True)

    # products.icon column
    if 'products' in tables:
        columns = [c['name'] for c in inspector.get_columns('products')]
        if 'icon' not in columns:
            op.add_column('products', sa.Column('icon', sa.String(10), nullable=True, server_default='\u2615'))  # ☕

    # stock_purchases table
    if 'stock_purchases' not in tables:
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
    # No destructive downgrade to avoid losing data inadvertently. Intentionally left as no-op.
    pass
