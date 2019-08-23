"""Add new abstract state

Revision ID: 0f20a5e4018e
Revises: 620b312814f3
Create Date: 2019-08-23 14:38:34.322010
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0f20a5e4018e'
down_revision = '620b312814f3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE event_abstracts.abstracts DROP CONSTRAINT ck_abstracts_valid_enum_state;

        ALTER TABLE event_abstracts.abstracts
        ADD CONSTRAINT ck_abstracts_valid_enum_state CHECK ((state = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7])));
    ''')


def downgrade():
    op.execute('''
        ALTER TABLE event_abstracts.abstracts DROP CONSTRAINT ck_abstracts_valid_enum_state;

        ALTER TABLE event_abstracts.abstracts
        ADD CONSTRAINT ck_abstracts_valid_enum_state CHECK ((state = ANY (ARRAY[1, 2, 3, 4, 5, 6])));
    ''')
