"""Migrate event labels from settings

Revision ID: a3295d628e3b
Revises: 266d78b1c5db
Create Date: 2020-03-24 10:04:10.926079
"""

import json
from collections import defaultdict
from uuid import uuid4

from alembic import context, op


# revision identifiers, used by Alembic.
revision = 'a3295d628e3b'
down_revision = '266d78b1c5db'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    # label definitions
    mapping = {}
    res = conn.execute("SELECT name, value FROM indico.settings WHERE module = 'event_labels'")
    for uuid, data in res:
        assert uuid == data['id']
        res2 = conn.execute("INSERT INTO events.labels (title, color) VALUES (%s, %s) RETURNING id",
                            (data['title'], data['color']))
        mapping[uuid] = res2.fetchone()[0]
    # event label assignments
    res = conn.execute('''
        SELECT event_id, name, value
        FROM events.settings
        WHERE module = 'label' AND name IN ('label', 'message');
    ''')
    event_data = defaultdict(dict)
    for event_id, name, value in res:
        event_data[event_id][name] = value
    for event_id, data in event_data.items():
        if not data.get('label'):
            continue
        label_id = mapping[data['label']]
        label_message = data.get('message', '')
        conn.execute("UPDATE events.events SET label_id = %s, label_message = %s WHERE id = %s",
                     (label_id, label_message, event_id))
    # cleanup
    conn.execute("DELETE FROM indico.settings WHERE module = 'event_labels'")
    conn.execute("DELETE FROM events.settings WHERE module = 'label'")


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    # label definitions
    mapping = {}
    res = conn.execute("SELECT id, title, color FROM events.labels")
    for label_id, title, color in res:
        uuid = unicode(uuid4())
        conn.execute("INSERT INTO indico.settings (module, name, value) VALUES ('event_labels', %s, %s)",
                     (uuid, json.dumps({'id': uuid, 'title': title, 'color': color})))
        mapping[label_id] = uuid
    # event label assignments
    res = conn.execute("SELECT id, label_id, label_message FROM events.events WHERE label_id IS NOT NULL")
    for event_id, label_id, label_message in res:
        uuid = mapping[label_id]
        stmt = "INSERT INTO events.settings (event_id, module, name, value) VALUES (%s, 'label', %s, %s)"
        conn.execute(stmt, (event_id, 'label', json.dumps(uuid)))
        if label_message:
            conn.execute(stmt, (event_id, 'message', json.dumps(label_message)))
    # cleanup
    conn.execute("UPDATE events.events SET label_id = NULL, label_message = '' WHERE label_id IS NOT NULL")
    conn.execute("DELETE FROM events.labels")
