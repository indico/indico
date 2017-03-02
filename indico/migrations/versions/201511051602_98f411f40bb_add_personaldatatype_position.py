"""Add PersonalDataType.position

Revision ID: 98f411f40bb
Revises: 468343faea20
Create Date: 2015-11-05 16:02:43.260085
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '98f411f40bb'
down_revision = '468343faea20'


def upgrade():
    op.drop_constraint('ck_form_items_valid_enum_personal_data_type', 'form_items', schema='event_registration')
    op.create_check_constraint('valid_enum_personal_data_type', 'form_items',
                               "personal_data_type IN ({})".format(', '.join(map(str, range(1, 10)))),
                               schema='event_registration')


def downgrade():
    op.drop_constraint('ck_form_items_valid_enum_personal_data_type', 'form_items', schema='event_registration')
    op.create_check_constraint('valid_enum_personal_data_type', 'form_items',
                               "personal_data_type IN ({})".format(', '.join(map(str, range(1, 9)))),
                               schema='event_registration')
