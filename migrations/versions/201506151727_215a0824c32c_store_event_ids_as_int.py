"""Store event ids as int

Revision ID: 215a0824c32c
Revises: 1041cc03dbe6
Create Date: 2015-06-11 10:16:33.841486
"""

import sqlalchemy as sa
from alembic import op, context


# revision identifiers, used by Alembic.
revision = '215a0824c32c'
down_revision = '1041cc03dbe6'


def _has_legacy_ids(table, column):
    conn = op.get_bind()
    return conn.execute(r"SELECT EXISTS(SELECT 1 FROM {0} WHERE {1} !~ '^[1-9]\d*$' AND {1} != '0')"
                        .format(table, column)).scalar()


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    if (_has_legacy_ids('events.settings', 'event_id') or _has_legacy_ids('events.settings_principals', 'event_id') or
            _has_legacy_ids('events.event_index', 'id')):
        raise Exception('Please run the legacy_events zodb importer first.')
    op.execute('ALTER TABLE events.event_index ALTER COLUMN id TYPE int USING id::int')
    op.execute('ALTER TABLE events.settings ALTER COLUMN event_id TYPE int USING event_id::int')
    op.execute('ALTER TABLE events.settings_principals ALTER COLUMN event_id TYPE int USING event_id::int')


def downgrade():
    op.alter_column('event_index', 'id', type_=sa.String, schema='events')
    op.alter_column('settings', 'event_id', type_=sa.String, schema='events')
    op.alter_column('settings_principals', 'event_id', type_=sa.String, schema='events')
