"""Add new abstract state

Revision ID: 0f20a5e4018e
Revises: 1b741c9123f6
Create Date: 2019-08-23 14:38:34.322010
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '0f20a5e4018e'
down_revision = '1b741c9123f6'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_abstracts_valid_enum_state', 'abstracts', schema='event_abstracts')
    op.create_check_constraint('valid_enum_state', 'abstracts',
                               '(state = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7]))', schema='event_abstracts')


def downgrade():
    op.drop_constraint('ck_abstracts_valid_enum_state', 'abstracts', schema='event_abstracts')
    op.create_check_constraint('valid_enum_state', 'abstracts',
                               '(state = ANY (ARRAY[1, 2, 3, 4, 5, 6]))', schema='event_abstracts')
