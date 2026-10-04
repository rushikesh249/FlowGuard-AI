"""add anomaly_runs table

Revision ID: f82c3a1567bc
Revises: a3b7c9d12e45
Create Date: 2026-08-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f82c3a1567bc'
down_revision: Union[str, Sequence[str], None] = 'a3b7c9d12e45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create anomaly_runs table."""
    op.create_table(
        'anomaly_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('upload_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('algorithm', sa.String(), nullable=False, server_default='isolation_forest'),
        sa.Column('contamination', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('n_anomalies', sa.Integer(), nullable=True),
        sa.Column('anomaly_rate', sa.Float(), nullable=True),
        sa.Column('model_path', sa.String(), nullable=True),
        sa.Column('results_path', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['upload_id'], ['uploaded_files.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_anomaly_runs_id'), 'anomaly_runs', ['id'], unique=False)


def downgrade() -> None:
    """Drop anomaly_runs table."""
    op.drop_index(op.f('ix_anomaly_runs_id'), table_name='anomaly_runs')
    op.drop_table('anomaly_runs')
