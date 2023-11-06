"""add_speakers_can_submit_to_events

Revision ID: 0acf26d68434
Revises: 31b699664893
Create Date: 2023-11-06 15:17:38.522399
"""

import sqlalchemy as sa
from alembic import op

from indico.modules.events.models.settings import EventSetting


# revision identifiers, used by Alembic.
revision = '0acf26d68434'
down_revision = '31b699664893'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('speakers_can_submit', sa.Boolean(), nullable=False,
                  server_default='false'), schema='events')
    op.alter_column('events', sa.Column('speakers_can_submit', server_default=None), schema='events')
    op.execute('''
        UPDATE events.events ev
        SET speakers_can_submit = true
        FROM events.settings es
        WHERE
        ev.id = es.event_id AND
        es.module = 'subcontributions' AND
        es.name = 'speakers_can_submit' AND
        es.value::bool;
    ''')
    op.execute('''
        DELETE FROM events.settings es
        WHERE
        es.module = 'subcontributions' AND
        es.name = 'speakers_can_submit';
    ''')


def downgrade():
    conn = op.get_bind()
    events_speakers_can_submit = conn.execute('''
        SELECT id FROM events.events ev
        WHERE
        ev.speakers_can_submit;
    ''')
    values = []
    for id in events_speakers_can_submit:
        values.append((id, 'subcontributions', 'speakers_can_submit', 'true'))
    stmt = sa.insert(EventSetting).values(
        [{'name': name, 'module': module, 'event_id': event_id, 'value': value} for event_id, module, name, value in values])
    op.execute(stmt)
    op.drop_column('events', 'speakers_can_submit', schema='events')
