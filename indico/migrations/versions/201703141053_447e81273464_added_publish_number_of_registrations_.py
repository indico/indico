"""added publish_number_of_registrations field to registartion form

Revision ID: 447e81273464
Revises: e185a5089262
Create Date: 2017-03-14 10:53:56.338986
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '447e81273464'
down_revision = 'e185a5089262'


def upgrade():
    op.add_column('forms', sa.Column('publish_number_of_registrations', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.alter_column('forms', 'publish_number_of_registrations', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'publish_number_of_registrations', schema='event_registration')
