"""Update constraint valid_enum_personal_data_type

Revision ID: 17996ef18cb9
Revises: 8e08236a529f
Create Date: 2024-01-30 15:31:42.810562
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '17996ef18cb9'
down_revision = '8e08236a529f'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_form_items_valid_enum_personal_data_type', 'form_items', schema='event_registration')
    op.create_check_constraint('valid_enum_personal_data_type', 'form_items',
                               '(personal_data_type = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))',
                               schema='event_registration')


def downgrade():
    op.drop_constraint('ck_form_items_valid_enum_personal_data_type', 'form_items', schema='event_registration')
    op.create_check_constraint('valid_enum_personal_data_type', 'form_items',
                               '(personal_data_type = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9]))',
                               schema='event_registration')
