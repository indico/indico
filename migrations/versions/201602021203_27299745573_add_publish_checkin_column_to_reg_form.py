"""Add publish_checkin column to reg form

Revision ID: 27299745573
Revises: 47a8b5324cd6
Create Date: 2016-02-02 12:03:15.973817
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '27299745573'
down_revision = '47a8b5324cd6'


def upgrade():
    op.add_column('forms', sa.Column('publish_checkin_enabled', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('forms', 'publish_checkin_enabled', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'publish_checkin_enabled', schema='event_registration')
