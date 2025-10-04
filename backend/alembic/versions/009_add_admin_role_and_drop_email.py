"""add admin role and drop email

Revision ID: 009_add_admin_and_drop_email
Revises: 008
Create Date: 2025-09-30
"""

from alembic import op
import sqlalchemy as sa

revision = '009_add_admin_and_drop_email'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum value 'admin' to userrole enum (Postgres specific)
    try:
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")
    except Exception:
        # SQLite or already added; ignore
        pass

    # Drop email column if exists
    with op.batch_alter_table('users') as batch_op:
        try:
            batch_op.drop_column('email')
        except Exception:
            pass


def downgrade():
    # Cannot easily remove enum value in Postgres; leave as-is.
    # Recreate email column (nullable) for downgrade compatibility
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))