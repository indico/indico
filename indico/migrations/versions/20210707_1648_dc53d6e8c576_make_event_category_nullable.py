"""Make event category nullable

Revision ID: dc53d6e8c576
Revises: 1cec32e42f65
Create Date: 2021-07-07 16:48:03.719901
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'dc53d6e8c576'
down_revision = '1cec32e42f65'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_events_category_data_set', 'events', schema='events')


def downgrade():
    op.create_check_constraint('category_data_set', 'events', 'category_id IS NOT NULL OR is_deleted', schema='events')
