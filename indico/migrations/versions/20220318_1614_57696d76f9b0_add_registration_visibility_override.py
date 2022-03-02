"""Add registration visibility override

Revision ID: 57696d76f9b0
Revises: 5123f24eb41e
Create Date: 2022-03-18 16:14:04.837722
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '57696d76f9b0'
down_revision = '5123f24eb41e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations',
                  sa.Column('participant_hidden', sa.Boolean(), server_default='false', nullable=False),
                  schema='event_registration')
    op.alter_column('registrations', 'participant_hidden', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'participant_hidden', schema='event_registration')
