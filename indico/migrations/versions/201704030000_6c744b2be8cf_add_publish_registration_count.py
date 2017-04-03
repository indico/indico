"""add publish_registration_count

Revision ID: 6c744b2be8cf
Revises: f15eac2175f8
Create Date: 2017-03-22 15:29:47.641528
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '6c744b2be8cf'
down_revision = 'f15eac2175f8'


def upgrade():
    op.add_column('forms', sa.Column('publish_registration_count', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.alter_column('forms', 'publish_registration_count', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'publish_registration_count', schema='event_registration')
