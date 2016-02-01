"""Add CHECK for category columns

Revision ID: ae00a6a1edd
Revises: ce6c3f7f35e
Create Date: 2016-02-04 10:36:57.350102
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'ae00a6a1edd'
down_revision = 'ce6c3f7f35e'


def upgrade():
    op.create_check_constraint('category_data_set', 'events',
                               '(category_id IS NOT NULL AND category_chain IS NOT NULL) OR is_deleted',
                               schema='events')


def downgrade():
    op.drop_constraint('ck_events_category_data_set', 'events', schema='events')
