from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    role_enum = postgresql.ENUM('user', 'admin', name='role_enum', create_type=False)
    order_status_enum = postgresql.ENUM('checking', 'verified', 'done', 'cancelled', name='order_status_enum', create_type=False)

    role_enum.create(op.get_bind(), checkfirst=True)
    order_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('customer_name', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', role_enum, nullable=False, server_default=sa.text("'user'")),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name_uz', sa.String(100), nullable=False, unique=True),
        sa.Column('name_ru', sa.String(100), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name_uz', sa.String(150), nullable=False),
        sa.Column('name_ru', sa.String(150), nullable=False),
        sa.Column('description_uz', sa.Text, nullable=True),
        sa.Column('description_ru', sa.Text, nullable=True),
        sa.Column('price', sa.Numeric(12,2), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', order_status_enum, nullable=False, server_default=sa.text("'checking'")),
        sa.Column('shipping_address', sa.String(255), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column('cancel_reason', sa.String(300), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_snapshot', postgresql.JSONB, nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('subtotal', sa.Numeric(12,2), nullable=False),
    )

def downgrade():
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')

    # 👇 PostgreSQL’ga mos drop
    postgresql.ENUM(name='order_status_enum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='role_enum').drop(op.get_bind(), checkfirst=True)