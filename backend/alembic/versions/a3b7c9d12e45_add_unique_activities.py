"""add unique_activities column

Revision ID: a3b7c9d12e45
Revises: 4557d408f194
Create Date: 2026-08-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b7c9d12e45'
down_revision: Union[str, Sequence[str], None] = '4557d408f194'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique_activities column to uploaded_files."""
    op.add_column('uploaded_files', sa.Column('unique_activities', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove unique_activities column from uploaded_files."""
    op.drop_column('uploaded_files', 'unique_activities')
