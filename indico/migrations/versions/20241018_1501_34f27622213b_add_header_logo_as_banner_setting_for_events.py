"""Add header_logo_as_banner setting for events

Revision ID: 34f27622213b
Revises: 75db3a4a4ed4
Create Date: 2024-10-18 15:01:53.443953
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '34f27622213b'
down_revision = '75db3a4a4ed4'
branch_labels = None
depends_on = None


def upgrade():
    # Make existing conferences with logos use the old header style
    op.execute('''
        INSERT INTO events.settings (module, name, event_id, value)
        SELECT 'layout', 'header_logo_as_banner', id, 'false'::jsonb
        FROM events.events WHERE type = 3 and logo_metadata != 'null'
        ON CONFLICT (module, name, event_id) DO NOTHING;
    ''')


def downgrade():
    op.execute('''
        DELETE FROM events.settings
        WHERE module = 'layout' AND name = 'header_logo_as_banner';
    ''')
