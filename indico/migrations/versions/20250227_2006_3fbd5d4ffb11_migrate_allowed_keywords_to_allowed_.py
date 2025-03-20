"""Migrate allowed_keywords to allowed_event_keywords

Revision ID: 3fbd5d4ffb11
Revises: c7d6c3641918
Create Date: 2025-02-27 20:06:16.910793
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3fbd5d4ffb11'
down_revision = 'c7d6c3641918'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE indico.settings
        SET name = 'allowed_event_keywords'
        WHERE module = 'events' AND name = 'allowed_keywords'
    ''')


def downgrade():
    op.execute('''
        UPDATE indico.settings
        SET name = 'allowed_keywords'
        WHERE module = 'events' AND name = 'allowed_event_keywords'
    ''')
