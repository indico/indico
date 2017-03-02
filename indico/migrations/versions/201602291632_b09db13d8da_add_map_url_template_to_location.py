"""Add map_url_template to location

Revision ID: b09db13d8da
Revises: 1aacd34201
Create Date: 2016-02-29 16:32:22.975647
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b09db13d8da'
down_revision = '1aacd34201'


def upgrade():
    op.add_column('locations', sa.Column('map_url_template', sa.String(), nullable=False, server_default=''),
                  schema='roombooking')
    op.alter_column('locations', 'map_url_template', server_default=None, schema='roombooking')


def downgrade():
    op.drop_column('locations', 'map_url_template', schema='roombooking')
