"""Add undone state to editing revisions

Revision ID: 5d05eda06776
Revises: 7551bd141960
Create Date: 2023-02-09 12:14:55.539279
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '5d05eda06776'
down_revision = '7551bd141960'
branch_labels = None
depends_on = None


class _FinalRevisionState(int, Enum):
    none = 0
    replaced = 1
    needs_submitter_confirmation = 2
    needs_submitter_changes = 3
    accepted = 4
    rejected = 5
    undone = 6


def upgrade():
    op.drop_constraint('ck_revisions_valid_enum_final_state', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_enum_final_state', 'revisions',
                               '(final_state = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6]))', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4,6)))', schema='event_editing')
    op.add_column('comments',
                  sa.Column('undone_judgment', PyIntEnum(_FinalRevisionState), nullable=False, server_default='0'),
                  schema='event_editing')
    op.alter_column('comments', 'undone_judgment', server_default=None, schema='event_editing')


def downgrade():
    op.drop_constraint('ck_revisions_valid_enum_final_state', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_enum_final_state', 'revisions',
                               '(final_state = ANY (ARRAY[0, 1, 2, 3, 4, 5]))', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4)))', schema='event_editing')
    op.drop_column('comments', 'undone_judgment', schema='event_editing')
