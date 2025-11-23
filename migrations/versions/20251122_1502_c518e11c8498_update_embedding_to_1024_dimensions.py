"""update_embedding_to_1024_dimensions

Revision ID: c518e11c8498
Revises: 2d2d9d11f77a
Create Date: 2025-11-22 15:02:12.290834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c518e11c8498'
down_revision = '2d2d9d11f77a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old 1536-dimension column
    op.execute('ALTER TABLE invoices DROP COLUMN IF EXISTS embedding')

    # Add new 1024-dimension column for BGE-Large
    op.execute('ALTER TABLE invoices ADD COLUMN embedding vector(1024)')


def downgrade() -> None:
    # Revert back to 1536 dimensions
    op.execute('ALTER TABLE invoices DROP COLUMN IF EXISTS embedding')
    op.execute('ALTER TABLE invoices ADD COLUMN embedding vector(1536)')
