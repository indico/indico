"""Add registration_form_id to designer templates

Revision ID: 4e32f4d5ebe4
Revises: b37cbc4bb129
Create Date: 2024-03-14 10:42:45.632227
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '4e32f4d5ebe4'
down_revision = 'b37cbc4bb129'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('registration_form_id', sa.Integer(), nullable=True), schema='indico')
    op.create_index(None, 'designer_templates', ['registration_form_id'], schema='indico')
    op.create_foreign_key(None, 'designer_templates', 'forms', ['registration_form_id'], ['id'],
                          source_schema='indico', referent_schema='event_registration')
    op.create_check_constraint('no_regform_if_category', 'designer_templates',
                               '(category_id IS NULL) OR (registration_form_id IS NULL)', schema='indico')


def downgrade():
    op.drop_constraint('ck_designer_templates_no_regform_if_category', 'designer_templates', schema='indico')
    op.drop_column('designer_templates', 'registration_form_id', schema='indico')
