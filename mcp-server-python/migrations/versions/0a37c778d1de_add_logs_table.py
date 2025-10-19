"""add_logs_table

Revision ID: 0a37c778d1de
Revises: 066d83dc6198
Create Date: 2025-10-20 00:07:13.332785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a37c778d1de'
down_revision: Union[str, None] = '066d83dc6198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create logs table
    op.create_table(
        'logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('ts', sa.BigInteger(), nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('operation', sa.String(50), nullable=True),
        sa.Column('method', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('correlation_id', sa.String(50), nullable=True),
        sa.Column('elapsed_sec', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL')
    )

    # Create indexes for common queries
    op.create_index('ix_logs_user_id', 'logs', ['user_id'])
    op.create_index('ix_logs_source_id', 'logs', ['source_id'])
    op.create_index('ix_logs_ts', 'logs', ['ts'])
    op.create_index('ix_logs_correlation_id', 'logs', ['correlation_id'])
    op.create_index('ix_logs_operation', 'logs', ['operation'])
    op.create_index('ix_logs_level', 'logs', ['level'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_logs_level')
    op.drop_index('ix_logs_operation')
    op.drop_index('ix_logs_correlation_id')
    op.drop_index('ix_logs_ts')
    op.drop_index('ix_logs_source_id')
    op.drop_index('ix_logs_user_id')

    # Drop table
    op.drop_table('logs')
