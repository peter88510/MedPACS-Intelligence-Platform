"""add measurement fields (instance device tags + ai_results measurement columns)

Revision ID: 7f3c9a2b1d04
Revises: 91725486ef55
Create Date: 2026-06-09 00:00:00.000000

Additive only (CLAUDE.md §12): all new columns are nullable or carry a
server_default, no drops/renames. Design: .work/ai_result_design.md §3.3.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7f3c9a2b1d04'
down_revision: Union[str, None] = '91725486ef55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # instances: raw device signal for the measurement-type resolver
    op.add_column('instances', sa.Column('device_manufacturer', sa.String(length=255), nullable=True))
    op.add_column('instances', sa.Column('device_model', sa.String(length=255), nullable=True))

    # ai_results: measurement-result fields. measurement_type carries a
    # server_default so existing rows (table currently empty) backfill cleanly.
    op.add_column(
        'ai_results',
        sa.Column('measurement_type', sa.String(length=32), nullable=False, server_default='excursion'),
    )
    op.add_column('ai_results', sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('ai_results', sa.Column('primary_value', sa.Float(), nullable=True))
    op.add_column('ai_results', sa.Column('primary_unit', sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_results', 'primary_unit')
    op.drop_column('ai_results', 'primary_value')
    op.drop_column('ai_results', 'result_json')
    op.drop_column('ai_results', 'measurement_type')
    op.drop_column('instances', 'device_model')
    op.drop_column('instances', 'device_manufacturer')
