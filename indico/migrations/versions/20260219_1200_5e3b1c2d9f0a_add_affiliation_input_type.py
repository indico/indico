"""Add affiliation input type to regform personal data

Revision ID: 5e3b1c2d9f0a
Revises: af9d03d7073c
Create Date: 2026-02-19 12:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '5e3b1c2d9f0a'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE event_registration.form_items
        SET input_type = 'affiliation',
            data = coalesce(data, '{}'::jsonb) || jsonb_build_object('affiliation_mode', 1)
        WHERE type = 5 AND personal_data_type = 4 AND input_type = 'text'
    ''')
    op.execute('''
        UPDATE event_registration.registration_data rd
        SET data = jsonb_build_object('id', null, 'text', rd.data #>> '{}')
        FROM event_registration.form_field_data ffd
        JOIN event_registration.form_items fi ON fi.id = ffd.field_id
        WHERE rd.field_data_id = ffd.id
            AND fi.input_type = 'affiliation'
            AND jsonb_typeof(rd.data) = 'string'
    ''')


def downgrade():
    op.execute('''
        UPDATE event_registration.registration_data rd
        SET data = to_jsonb(coalesce(rd.data->>'text', ''))
        FROM event_registration.form_field_data ffd
        JOIN event_registration.form_items fi ON fi.id = ffd.field_id
        WHERE rd.field_data_id = ffd.id
            AND fi.input_type = 'affiliation'
            AND jsonb_typeof(rd.data) = 'object'
            AND rd.data ? 'text'
    ''')
    op.execute('''
        UPDATE event_registration.form_items
        SET input_type = 'text',
            data = coalesce(data, '{}'::jsonb) - 'affiliation_mode'
        WHERE input_type = 'affiliation'
    ''')
