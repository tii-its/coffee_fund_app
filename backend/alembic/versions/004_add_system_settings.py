"""Add system_settings table for PIN storage

Revision ID: 004
Revises: 003
Create Date: 2024-09-27 20:00:00.000000

NOTE: Normalized during duplicate 004 cleanup.
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
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_encrypted', sa.Boolean, server_default=sa.text('false'), nullable=False),
    )
    
    # Create unique index on key
    op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=True)
    

def downgrade() -> None:
    # Drop the table
    op.drop_table('system_settings')