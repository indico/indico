"""Fix user name_format values

Revision ID: 9b3fc740b722
Revises: 5d05eda06776
Create Date: 2023-07-12 17:42:02.247869
"""

import json

from alembic import op


# revision identifiers, used by Alembic.
revision = '9b3fc740b722'
down_revision = '5d05eda06776'
branch_labels = None
depends_on = None


mapping = {
    0: 'first_last',
    1: 'last_first',
    2: 'last_f',
    3: 'f_last',
    4: 'first_last_upper',
    5: 'last_first_upper',
    6: 'last_f_upper',
    7: 'f_last_upper'
}


def upgrade():
    for value, name in mapping.items():
        op.execute(f'''
            UPDATE users.settings
            SET value = '{json.dumps(name)}'
            WHERE module = 'users' AND name = 'name_format' AND value = '{value}'
        ''')  # noqa: S608


def downgrade():
    for value, name in mapping.items():
        op.execute(f'''
            UPDATE users.settings
            SET value = '{json.dumps(value)}'
            WHERE module = 'users' AND name = 'name_format' AND value = '{json.dumps(name)}'
        ''')  # noqa: S608
