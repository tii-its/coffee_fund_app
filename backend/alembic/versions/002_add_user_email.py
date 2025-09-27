"""Add email field to users table

Revision ID: 002
Revises: 001
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email column to users table
    op.add_column('users', sa.Column('email', sa.String(320), nullable=True))
    
    # Create a unique index on email
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Update existing users with placeholder emails (for development only)
    # In production, this would need proper data migration
    op.execute("""
        UPDATE users 
        SET email = CONCAT(LOWER(REPLACE(display_name, ' ', '.')), '@example.com')
        WHERE email IS NULL
    """)
    
    # Now make email column not nullable
    op.alter_column('users', 'email', nullable=False)


def downgrade() -> None:
    # Remove email column and its index
    op.drop_index('ix_users_email', table_name='users')
    op.drop_column('users', 'email')