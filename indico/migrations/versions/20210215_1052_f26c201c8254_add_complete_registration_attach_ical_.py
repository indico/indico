"""Add complete_registration_attach_ical to RegistrationForm

Revision ID: f26c201c8254
Revises: 26985db8ed12
Create Date: 2021-02-15 10:52:15.353452
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f26c201c8254'
down_revision = '26985db8ed12'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('complete_registration_attach_ical', sa.Boolean(), nullable=False, server_default='false'), schema='event_registration')
    op.alter_column('forms', 'complete_registration_attach_ical', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'complete_registration_attach_ical', schema='event_registration')
