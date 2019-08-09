"""Migrate indico-weeks-view theme name

Revision ID: 620b312814f3
Revises: 06a4ec717b84
Create Date: 2019-08-09 17:11:55.699189
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '620b312814f3'
down_revision = '06a4ec717b84'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE events.settings
        SET value = '"indico_weeks_view"'::json
        WHERE module = 'layout' AND name = 'timetable_theme' AND value #>> '{}' = 'indico-weeks-view';
    ''')


def downgrade():
    op.execute('''
        UPDATE events.settings
        SET value = '"indico-weeks-view"'::json
        WHERE module = 'layout' AND name = 'timetable_theme' AND value #>> '{}' = 'indico_weeks_view';
    ''')
