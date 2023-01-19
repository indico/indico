"""Add undone state to editing revisions

Revision ID: 5d05eda06776
Revises: b45847c0e62f
Create Date: 2023-01-12 11:16:55.539279
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '5d05eda06776'
down_revision = 'b45847c0e62f'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_revisions_valid_enum_final_state', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_enum_final_state', 'revisions',
                               '(final_state = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6]))', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4,6)))', schema='event_editing')


def downgrade():
    op.drop_constraint('ck_revisions_valid_enum_final_state', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_enum_final_state', 'revisions',
                               '(final_state = ANY (ARRAY[0, 1, 2, 3, 4, 5]))', schema='event_editing')
    op.drop_constraint('ck_revisions_valid_state_combination', 'revisions', schema='event_editing')
    op.create_check_constraint('valid_state_combination', 'revisions',
                               '(initial_state=1 AND final_state IN (0,1)) OR (initial_state=2) OR '
                               '(initial_state=3 AND (final_state IN (0,3,4)))', schema='event_editing')
