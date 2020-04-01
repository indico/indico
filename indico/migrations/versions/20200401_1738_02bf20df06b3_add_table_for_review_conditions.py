"""Add table for review conditions

Revision ID: 02bf20df06b3
Revises: 3c5462aef0b7
Create Date: 2020-04-01 17:38:54.405431
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.editing.models.editable import EditableType


# revision identifiers, used by Alembic.
revision = '02bf20df06b3'
down_revision = '3c5462aef0b7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'review_conditions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', PyIntEnum(EditableType), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_editing',
    )
    op.create_table(
        'review_condition_file_types',
        sa.Column('review_condition_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('file_type_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.ForeignKeyConstraint(
            ['file_type_id'],
            ['event_editing.file_types.id'],
        ),
        sa.ForeignKeyConstraint(
            ['review_condition_id'],
            ['event_editing.review_conditions.id'],
        ),
        sa.PrimaryKeyConstraint('review_condition_id', 'file_type_id'),
        schema='event_editing',
    )


def downgrade():
    op.drop_table('review_condition_file_types', schema='event_editing')
    op.drop_table('review_conditions', schema='event_editing')
