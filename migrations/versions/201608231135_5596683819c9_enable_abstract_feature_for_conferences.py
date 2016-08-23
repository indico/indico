"""Enable abstract feature for conferences

Revision ID: 5596683819c9
Revises: ccd9d0858ff
Create Date: 2016-08-23 11:35:26.018462
"""

import json

import sqlalchemy as sa
from alembic import context, op


# revision identifiers, used by Alembic.
revision = '5596683819c9'
down_revision = 'ccd9d0858ff'

_update_setting_query = 'UPDATE events.settings SET value = :value WHERE id = :id'


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')

    conn = op.get_bind()
    query = '''
        SELECT s.id, s.value
        FROM events.settings s
        JOIN events.events e ON (e.id = s.event_id)
        WHERE
            module = 'features' AND
            name = 'enabled' AND
            value::jsonb != 'null'::jsonb AND
            NOT (value::jsonb ? 'abstracts') AND
            e.type = 3;

    '''

    res = conn.execute(query)
    for id_, value in res:
        value = sorted(value + ['abstracts'])
        conn.execute(sa.text(_update_setting_query).bindparams(id=id_, value=json.dumps(value)))


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')

    conn = op.get_bind()
    query = '''
        SELECT id, value
        FROM events.settings
        WHERE
            module = 'features' AND
            name = 'enabled' AND
            value::jsonb != 'null'::jsonb AND
            value::jsonb ? 'abstracts';
    '''

    res = conn.execute(query)
    for id_, value in res:
        value = sorted(set(value) - {'abstracts'})
        conn.execute(sa.text(_update_setting_query).bindparams(id=id_, value=json.dumps(value)))
