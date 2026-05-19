"""add_ai_results_table

Revision ID: 91725486ef55
Revises: e25c80289a9c
Create Date: 2026-05-19 08:12:15.402184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91725486ef55'
down_revision: Union[str, None] = 'e25c80289a9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 3 task #10: AIResult table for AI segmentation results
    # PLAN §9.3 schema; nullable mask_path/confidence/error_message reflect
    # status transitions (queued -> running -> completed/failed).
    op.create_table(
        'ai_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=64), nullable=False),
        sa.Column('model_version', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('mask_path', sa.String(length=512), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id'], name='fk_ai_results_instance_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_results_id'), 'ai_results', ['id'], unique=False)
    op.create_index(op.f('ix_ai_results_instance_id'), 'ai_results', ['instance_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_results_instance_id'), table_name='ai_results')
    op.drop_index(op.f('ix_ai_results_id'), table_name='ai_results')
    op.drop_table('ai_results')
