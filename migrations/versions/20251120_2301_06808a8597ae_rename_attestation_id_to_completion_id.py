"""rename_attestation_id_to_completion_id

Revision ID: 06808a8597ae
Revises: 88c3566b9a0b
Create Date: 2025-11-20 23:01:43.229544

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06808a8597ae'
down_revision = '88c3566b9a0b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename attestation_id to completion_id in conversations table
    op.alter_column('conversations', 'attestation_id', new_column_name='completion_id')


def downgrade() -> None:
    # Revert: rename completion_id back to attestation_id
    op.alter_column('conversations', 'completion_id', new_column_name='attestation_id')
