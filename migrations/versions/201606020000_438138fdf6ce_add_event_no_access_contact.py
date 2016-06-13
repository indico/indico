"""Add event no_access_contact and access_key

Revision ID: 438138fdf6ce
Revises: 3032079d8b33
Create Date: 2016-06-10 14:04:06.332491
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '438138fdf6ce'
down_revision = '3032079d8b33'


def upgrade():
    op.add_column('events', sa.Column('no_access_contact', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.add_column('events', sa.Column('access_key', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.alter_column('events', 'no_access_contact', server_default=None, schema='events')
    op.alter_column('events', 'access_key', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'access_key', schema='events')
    op.drop_column('events', 'no_access_contact', schema='events')
