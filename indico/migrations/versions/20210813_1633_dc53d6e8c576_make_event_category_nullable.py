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
    op.create_check_constraint('unlisted_events_always_inherit', 'events',
                               'is_deleted OR category_id IS NOT NULL OR protection_mode = 1',
                               schema='events')


def downgrade():
    op.execute('SET CONSTRAINTS ALL IMMEDIATE')
    op.execute('''
        UPDATE events.events
        SET is_deleted = true
        WHERE category_id IS NULL AND NOT is_deleted
    ''')
    op.execute('''
        ALTER TABLE events.events
        ADD CONSTRAINT "ck_events_category_data_set"
        CHECK (category_id IS NOT NULL OR is_deleted)
    ''')
    op.drop_constraint('ck_events_unlisted_events_always_inherit', 'events', schema='events')
