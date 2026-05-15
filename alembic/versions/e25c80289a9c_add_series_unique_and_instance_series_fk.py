"""add_series_unique_and_instance_series_fk

Revision ID: e25c80289a9c
Revises: 20809e26d134
Create Date: 2026-05-15 10:09:20.693752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e25c80289a9c'
down_revision: Union[str, None] = '20809e26d134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Series.series_instance_uid: nullable→NOT NULL, recreate index as UNIQUE.
    #    Safe because series table is currently empty (upload pipeline never wrote to it).
    op.alter_column('series', 'series_instance_uid',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=False)
    op.drop_index('ix_series_series_instance_uid', table_name='series')
    op.create_index(op.f('ix_series_series_instance_uid'), 'series', ['series_instance_uid'], unique=True)

    # 2. Instances: add series_instance_uid column + FK + index.
    #    Nullable for back-compat with existing rows (NULL means pre-FK upload).
    op.add_column('instances', sa.Column('series_instance_uid', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_instances_series_instance_uid'), 'instances', ['series_instance_uid'], unique=False)
    op.create_foreign_key(
        'fk_instances_series_instance_uid',
        'instances', 'series',
        ['series_instance_uid'], ['series_instance_uid']
    )


def downgrade() -> None:
    # Reverse order: drop instances FK/column first, then revert series.
    op.drop_constraint('fk_instances_series_instance_uid', 'instances', type_='foreignkey')
    op.drop_index(op.f('ix_instances_series_instance_uid'), table_name='instances')
    op.drop_column('instances', 'series_instance_uid')

    op.drop_index(op.f('ix_series_series_instance_uid'), table_name='series')
    op.create_index('ix_series_series_instance_uid', 'series', ['series_instance_uid'], unique=False)
    op.alter_column('series', 'series_instance_uid',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=True)
