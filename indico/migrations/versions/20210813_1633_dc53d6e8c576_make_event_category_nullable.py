"""Make event category nullable

Revision ID: dc53d6e8c576
Revises: 9d00917b2fa8
Create Date: 2021-07-07 16:48:03.719901
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'dc53d6e8c576'
down_revision = '9d00917b2fa8'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_events_category_data_set', 'events', schema='events')


def downgrade():
    op.create_check_constraint('category_data_set', 'events', 'category_id IS NOT NULL OR is_deleted', schema='events')
