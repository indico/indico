"""Fix purged accommodation fields

Revision ID: 7551bd141960
Revises: b45847c0e62f
Create Date: 2023-01-31 12:54:25.070817
"""

import json

from alembic import context, op

from indico.util.string import snakify_keys


# revision identifiers, used by Alembic.
revision = '7551bd141960'
down_revision = 'b45847c0e62f'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    res = conn.execute('''
        SELECT rd.registration_id, rd.field_data_id, rd.data
        FROM event_registration.registration_data rd
        JOIN event_registration.form_field_data ffd ON (ffd.id = rd.field_data_id)
        join event_registration.form_items fi ON (fi.id = ffd.field_id)
        WHERE fi.input_type = 'accommodation' AND rd.data ? 'isNoAccommodation';
    ''')
    for registration_id, field_data_id, data in res:
        conn.execute('''
            UPDATE event_registration.registration_data
            SET data = %s
            WHERE registration_id = %s AND field_data_id = %s
        ''', (json.dumps(snakify_keys(data))), registration_id, field_data_id)


def downgrade():
    pass
