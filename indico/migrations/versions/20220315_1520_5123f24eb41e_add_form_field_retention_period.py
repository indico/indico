"""Add retention period to RegistrationFormItem

Revision ID: 5123f24eb41e
Revises: ef7a8b2e6737
Create Date: 2022-03-15 15:20:59.230835
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '5123f24eb41e'
down_revision = 'ef7a8b2e6737'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('form_items',
                  sa.Column('retention_period', sa.Interval(), nullable=True),
                  schema='event_registration')
    op.create_check_constraint('retention_period_allowed_fields', 'form_items',
                               'retention_period IS NULL OR '
                               'type = 2 OR (type = 5 AND personal_data_type NOT IN (1, 2, 3))',
                               schema='event_registration')
    op.add_column('form_items',
                  sa.Column('is_purged', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('form_items', 'is_purged', server_default=None, schema='event_registration')


def downgrade():
    op.drop_constraint('ck_form_items_retention_period_allowed_fields', 'form_items', schema='event_registration')
    op.drop_column('form_items', 'retention_period', schema='event_registration')
    op.drop_column('form_items', 'is_purged', schema='event_registration')
