"""refactor_models_remove_auth_add_i18n

Revision ID: cd76d1c8dfac
Revises: 0001_init
Create Date: 2025-11-25 06:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd76d1c8dfac'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade():
    # Categories
    op.add_column('categories', sa.Column('name_en', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_categories_name_en'), 'categories', ['name_en'], unique=True)
    
    # Products
    op.add_column('products', sa.Column('name_en', sa.String(length=150), nullable=True))
    op.add_column('products', sa.Column('description_en', sa.Text(), nullable=True))
    
    # Users
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    
    # Drop email and password_hash
    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.drop_column('users', 'email')
    op.drop_column('users', 'password_hash')


def downgrade():
    # Users
    op.add_column('users', sa.Column('password_hash', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.create_unique_constraint('users_email_key', 'users', ['email'])
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_column('users', 'telegram_id')
    
    # Products
    op.drop_column('products', 'description_en')
    op.drop_column('products', 'name_en')
    
    # Categories
    op.drop_index(op.f('ix_categories_name_en'), table_name='categories')
    op.drop_column('categories', 'name_en')
