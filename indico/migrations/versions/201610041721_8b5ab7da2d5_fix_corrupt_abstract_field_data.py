"""Fix corrupt abstract field data

Revision ID: 8b5ab7da2d5
Revises: 52d970fb6a74
Create Date: 2016-10-04 17:21:19.186125
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '8b5ab7da2d5'
down_revision = '52d970fb6a74'


def upgrade():
    # We don't want any dicts in abstract field values...
    # Single choice fields with no value should be `null`, text fields should be empty
    op.execute('''
        UPDATE event_abstracts.abstract_field_values fv
        SET data = 'null'::json
        FROM events.contribution_fields cf
        WHERE data::jsonb = '{}'::jsonb AND cf.id = fv.contribution_field_id AND cf.field_type = 'single_choice';

        UPDATE event_abstracts.abstract_field_values fv
        SET data = '""'::json
        FROM events.contribution_fields cf
        WHERE data::jsonb = '{}'::jsonb AND cf.id = fv.contribution_field_id AND cf.field_type = 'text';
    ''')


def downgrade():
    pass
