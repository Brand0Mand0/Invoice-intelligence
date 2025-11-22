"""add_category_purchaser_recurring_to_invoices

Revision ID: 3304a96e46c6
Revises: 06808a8597ae
Create Date: 2025-11-21 09:41:21.918504

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3304a96e46c6'
down_revision = '06808a8597ae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add business intelligence fields to invoices table
    op.add_column('invoices', sa.Column('category', sa.String(100), nullable=True, server_default='Other'))
    op.add_column('invoices', sa.Column('purchaser', sa.String(100), nullable=True))
    op.add_column('invoices', sa.Column('is_recurring', sa.Boolean(), nullable=True, server_default='false'))

    # Create indexes for faster querying
    op.create_index('ix_invoices_category', 'invoices', ['category'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_invoices_category', 'invoices')

    # Remove columns
    op.drop_column('invoices', 'is_recurring')
    op.drop_column('invoices', 'purchaser')
    op.drop_column('invoices', 'category')
