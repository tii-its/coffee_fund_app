"""Add email to users table

Revision ID: 002
Revises: 001
Create Date: 2024-09-27 18:40:00.000000

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
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
    
    # Update existing users with a default email pattern (required for migration)
    op.execute("UPDATE users SET email = display_name || '@coffee-fund.local' WHERE email IS NULL")
    
    # Make email non-nullable and add unique constraint
    op.alter_column('users', 'email', nullable=False)
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    op.create_index('ix_users_email', 'users', ['email'])


def downgrade() -> None:
    # Remove email column and constraints
    op.drop_index('ix_users_email', 'users')
    op.drop_constraint('uq_users_email', 'users')
    op.drop_column('users', 'email')