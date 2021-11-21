"""Remove is_billable from registration fields

Revision ID: 3dafee32ba7d
Revises: 84874a17eaf3
Create Date: 2021-11-21 14:03:26.901129
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3dafee32ba7d'
down_revision = '84874a17eaf3'
branch_labels = None
depends_on = None


def upgrade():
    # Remove is_billable from top-level data
    op.execute('''
        UPDATE event_registration.form_field_data
        SET versioned_data = versioned_data - 'is_billable'
        WHERE versioned_data ? 'is_billable';
    ''')

    # Do the same for choices
    op.execute('''
        WITH choices AS (
            SELECT
                id,
                jsonb_agg(item - 'is_billable' ORDER BY index) AS data
            FROM
                event_registration.form_field_data,
                jsonb_array_elements(versioned_data -> 'choices') WITH ORDINALITY choice_ord(item, index)
            GROUP BY id
        )
        UPDATE event_registration.form_field_data fd
        SET versioned_data = fd.versioned_data || jsonb_build_object('choices', c.data)
        FROM choices c
        WHERE fd.id = c.id;
    ''')


def downgrade():
    # Restore is_billable in choices (when there's a price)
    op.execute('''
        WITH choices AS (
            SELECT
                id,
                jsonb_agg(item || jsonb_build_object('is_billable', (item ->> 'price')::decimal > 0) ORDER BY index) AS data
            FROM
                event_registration.form_field_data,
                jsonb_array_elements(versioned_data -> 'choices') WITH ORDINALITY choice_ord(item, index)
            GROUP BY id
        )
        UPDATE event_registration.form_field_data fd
        SET versioned_data = fd.versioned_data || jsonb_build_object('choices', c.data)
        FROM choices c
        WHERE fd.id = c.id;
    ''')

    # Do likewise for top-level data
    op.execute('''
        UPDATE event_registration.form_field_data
        SET versioned_data = versioned_data || jsonb_build_object('is_billable', (versioned_data ->> 'price')::decimal > 0)
        WHERE versioned_data ? 'price';
    ''')
