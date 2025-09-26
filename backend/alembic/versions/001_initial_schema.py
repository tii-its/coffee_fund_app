"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums with checkfirst=True to avoid conflicts
    userrole_enum = postgresql.ENUM('user', 'treasurer', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)
    
    moneymovetype_enum = postgresql.ENUM('deposit', 'payout', name='moneymovetype') 
    moneymovetype_enum.create(op.get_bind(), checkfirst=True)
    
    moneymovestatus_enum = postgresql.ENUM('pending', 'confirmed', 'rejected', name='moneymovestatus')
    moneymovestatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('qr_code', sa.String(255), nullable=True),
        sa.Column('role', userrole_enum, nullable=False),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('price_cents', sa.Integer, nullable=False),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create consumptions table
    op.create_table(
        'consumptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('qty', sa.Integer, nullable=False),
        sa.Column('unit_price_cents', sa.Integer, nullable=False),
        sa.Column('amount_cents', sa.Integer, nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
    )
    
    # Create money_moves table
    op.create_table(
        'money_moves',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('type', moneymovetype_enum, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount_cents', sa.Integer, nullable=False),
        sa.Column('note', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', moneymovestatus_enum, server_default=sa.text("'pending'"), nullable=False),
    )
    
    # Create audit table
    op.create_table(
        'audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('meta_json', postgresql.JSONB, nullable=True),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_users_display_name', 'users', ['display_name'])
    op.create_index('ix_users_qr_code', 'users', ['qr_code'])
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_consumptions_user_id', 'consumptions', ['user_id'])
    op.create_index('ix_consumptions_product_id', 'consumptions', ['product_id'])
    op.create_index('ix_consumptions_at', 'consumptions', ['at'])
    op.create_index('ix_money_moves_user_id', 'money_moves', ['user_id'])
    op.create_index('ix_money_moves_status', 'money_moves', ['status'])
    op.create_index('ix_money_moves_type', 'money_moves', ['type'])
    op.create_index('ix_audit_actor_id', 'audit', ['actor_id'])
    op.create_index('ix_audit_entity', 'audit', ['entity'])
    op.create_index('ix_audit_at', 'audit', ['at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_at', 'audit')
    op.drop_index('ix_audit_entity', 'audit')
    op.drop_index('ix_audit_actor_id', 'audit')
    op.drop_index('ix_money_moves_type', 'money_moves')
    op.drop_index('ix_money_moves_status', 'money_moves')
    op.drop_index('ix_money_moves_user_id', 'money_moves')
    op.drop_index('ix_consumptions_at', 'consumptions')
    op.drop_index('ix_consumptions_product_id', 'consumptions')
    op.drop_index('ix_consumptions_user_id', 'consumptions')
    op.drop_index('ix_products_name', 'products')
    op.drop_index('ix_users_qr_code', 'users')
    op.drop_index('ix_users_display_name', 'users')
    
    # Drop tables
    op.drop_table('audit')
    op.drop_table('money_moves')
    op.drop_table('consumptions')
    op.drop_table('products')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS moneymovestatus')
    op.execute('DROP TYPE IF EXISTS moneymovetype')
    op.execute('DROP TYPE IF EXISTS userrole')