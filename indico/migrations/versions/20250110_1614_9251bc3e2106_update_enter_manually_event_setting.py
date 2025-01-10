"""Update enter_manually event setting

Revision ID: 9251bc3e2106
Revises: 379ba72f4096
Create Date: 2025-01-10 16:14:46.170271
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '9251bc3e2106'
down_revision = '379ba72f4096'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE events.settings
        SET name = 'custom_persons_mode'
        WHERE module = 'persons' AND name = 'disallow_custom_persons'
    ''')
    op.execute('''
        UPDATE events.settings
        SET value = '"always"'::jsonb
        WHERE module = 'persons' AND name = 'custom_persons_mode' AND value = 'false'::jsonb;
    ''')
    op.execute('''
        UPDATE events.settings
        SET value = '"never"'::jsonb
        WHERE module = 'persons' AND name = 'custom_persons_mode' AND value = 'true'::jsonb;
    ''')


def downgrade():
    op.execute('''
        UPDATE events.settings
        SET name = 'disallow_custom_persons'
        WHERE module = 'persons' AND name = 'custom_persons_mode'
    ''')
    op.execute('''
        UPDATE events.settings
        SET value = 'true'::jsonb
        WHERE module = 'persons' AND name = 'disallow_custom_persons' AND value #>> '{}' != 'always';
    ''')
    op.execute('''
        UPDATE events.settings
        SET value = 'false'::jsonb
        WHERE module = 'persons' AND name = 'disallow_custom_persons' AND value #>> '{}' = 'always';
    ''')
