"""Add stock_purchases table

Revision ID: 004
Revises: 003
Create Date: 2025-09-27 20:15:00.000000

NOTE: Renamed from conflicting '002' to '004' after merge to resolve duplicate revision ID.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create stock_purchases table
    op.create_table(
        'stock_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('item_name', sa.String(255), nullable=False, index=True),
        sa.Column('supplier', sa.String(255), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price_cents', sa.Integer, nullable=False),
        sa.Column('total_amount_cents', sa.Integer, nullable=False),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('receipt_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_cash_out_processed', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('stock_purchases')