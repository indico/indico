"""Fix regform old accommodation fields

Revision ID: bc4e7682e7df
Revises: 2963fba57558
Create Date: 2017-04-24 16:04:07.476843
"""

import json
import uuid
import itertools
from operator import attrgetter

from alembic import context, op

# revision identifiers, used by Alembic.
revision = 'bc4e7682e7df'
down_revision = '2963fba57558'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()

    field_data_query = conn.execute("""
        SELECT ffd.field_id, ffd.id, fi.is_required, ffd.versioned_data, fi.data
        FROM event_registration.form_field_data ffd
        JOIN event_registration.form_items fi ON fi.id = ffd.field_id
        WHERE fi.input_type = 'accommodation' AND NOT fi.is_deleted
        ORDER BY ffd.field_id
    """)

    for field_id, data in itertools.groupby(field_data_query, attrgetter('field_id')):
        choice_id = unicode(uuid.uuid4())
        needs_caption = False
        for row in data:
            if not any(('is_no_accommodation' in choice) for choice in row.versioned_data['choices']):
                needs_caption = True
                no_acc_choice = {'is_no_accommodation': True,
                                 'is_enabled': not row.is_required,
                                 'price': 0,
                                 'is_billable': False,
                                 'places_limit': 0,
                                 'placeholder': 'Title of the "None" option',
                                 'id': choice_id}

                row.versioned_data['choices'] += [no_acc_choice]
                conn.execute("UPDATE event_registration.form_field_data SET versioned_data = %s WHERE id = %s",
                             (json.dumps(row.versioned_data), row.id))
        if needs_caption:
            row.data['captions'][choice_id] = 'No accommodation'
            conn.execute("UPDATE event_registration.form_items SET data = %s WHERE id = %s",
                         (json.dumps(row.data), field_id))


def downgrade():
    pass
