"""Separate comment into initial and final

Revision ID: aad32911e9df
Revises: b3ce69ab24d9
Create Date: 2020-03-16 15:15:40.885457
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'aad32911e9df'
down_revision = 'b3ce69ab24d9'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(table_name='revisions', column_name='comment', new_column_name='initial_comment', schema='event_editing')
    op.add_column('revisions', sa.Column('final_comment', sa.Text(), nullable=False, server_default=''), schema='event_editing')
    op.alter_column('revisions', column_name='final_comment', server_default=None, schema='event_editing')


def downgrade():
    op.drop_column('revisions', 'final_comment', schema='event_editing')
    op.alter_column('revisions', 'initial_comment', new_column_name='comment', schema='event_editing')
