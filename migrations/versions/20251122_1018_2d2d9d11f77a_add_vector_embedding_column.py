"""add_vector_embedding_column

Revision ID: 2d2d9d11f77a
Revises: 3304a96e46c6
Create Date: 2025-11-22 10:18:04.748900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d2d9d11f77a'
down_revision = '3304a96e46c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add embedding column (1536 dimensions for OpenAI text-embedding-ada-002)
    op.execute('ALTER TABLE invoices ADD COLUMN embedding vector(1536)')

    # Note: IVFFlat index requires data in the table before creation
    # We'll create it manually later with:
    # CREATE INDEX invoices_embedding_idx ON invoices USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    # For now, queries will use sequential scan (fine for <10K invoices)


def downgrade() -> None:
    # Drop index first
    op.execute('DROP INDEX IF EXISTS invoices_embedding_idx')

    # Drop column
    op.execute('ALTER TABLE invoices DROP COLUMN IF EXISTS embedding')

    # Note: We don't drop the extension as other tables might use it
