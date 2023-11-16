"""Add subcontrib_speakers_can_submit to events table

Revision ID: 0acf26d68434
Revises: 31b699664893
Create Date: 2023-11-06 15:17:38.522399
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0acf26d68434'
down_revision = '31b699664893'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('subcontrib_speakers_can_submit', sa.Boolean(), nullable=False,
                                      server_default='false'), schema='events')
    op.alter_column('events', 'subcontrib_speakers_can_submit', server_default=None, schema='events')
    op.execute('''
        UPDATE events.events ev
        SET subcontrib_speakers_can_submit = true
        FROM events.settings es
        WHERE
            ev.id = es.event_id AND
            es.module = 'subcontributions' AND
            es.name = 'speakers_can_submit' AND
            es.value = 'true'::jsonb
    ''')
    op.execute('''
        DELETE FROM events.settings WHERE module = 'subcontributions' AND name = 'speakers_can_submit'
    ''')


def downgrade():
    conn = op.get_bind()
    conn.execute('''
        INSERT INTO events.settings (module, name, event_id, value)
        SELECT 'subcontributions', 'speakers_can_submit', id, 'true'::jsonb
        FROM events.events WHERE subcontrib_speakers_can_submit
    ''')
    op.drop_column('events', 'subcontrib_speakers_can_submit', schema='events')
