"""Cleanup registration fields is_billable

Revision ID: 84874a17eaf3
Revises: 8993132179d3
Create Date: 2021-11-19 15:39:49.401820
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '84874a17eaf3'
down_revision = '8993132179d3'
branch_labels = None
depends_on = None


def upgrade():
    # Set negative prices to zero
    op.execute('''
        UPDATE event_registration.form_field_data
        SET versioned_data = versioned_data || jsonb_build_object('price', 0)
        WHERE (versioned_data ->> 'price')::decimal < 0;
    ''')

    # Make free fields non-billable
    op.execute('''
        UPDATE event_registration.form_field_data
        SET versioned_data = versioned_data || jsonb_build_object('is_billable', false)
        WHERE (versioned_data ->> 'is_billable')::bool AND (versioned_data ->> 'price')::decimal = 0;
    ''')

    # Set price to zero for non-billable fields
    op.execute('''
        UPDATE event_registration.form_field_data
        SET versioned_data = versioned_data || jsonb_build_object('price', 0)
        WHERE NOT (versioned_data ->> 'is_billable')::bool AND (versioned_data ->> 'price')::decimal != 0;
    ''')

    # Do the same for choices
    op.execute('''
        WITH choices AS (
            SELECT
                id,
                jsonb_agg(item || jsonb_build_object(
                    'price', CASE WHEN (item ->> 'is_billable')::bool THEN greatest(0, (item ->> 'price')::decimal) ELSE 0 END,
                    'is_billable', (item ->> 'price')::decimal > 0 AND (item ->> 'is_billable')::bool
                ) ORDER BY index) AS data
            FROM
                event_registration.form_field_data,
                jsonb_array_elements(versioned_data -> 'choices') WITH ORDINALITY choice_ord(item, index)
            GROUP BY id
        )
        UPDATE event_registration.form_field_data fd
        SET versioned_data = fd.versioned_data || jsonb_build_object('choices', c.data)
        FROM choices c
        WHERE fd.id = c.id AND EXISTS (
            SELECT 1
            FROM event_registration.form_field_data fd2
            INNER JOIN LATERAL jsonb_array_elements(versioned_data -> 'choices') choice ON true
            WHERE
                fd2.id = fd.id AND
                fd2.versioned_data ? 'choices' AND (
                    (choice ->> 'price')::decimal < 0 OR
                    (choice ->> 'is_billable')::bool AND (choice ->> 'price')::decimal <= 0 OR
                    NOT (choice ->> 'is_billable')::bool AND (choice ->> 'price')::decimal != 0
                )
        );
    ''')


def downgrade():
    pass
