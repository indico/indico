"""Add new ip network group columns

Revision ID: 459e5ec98b96
Revises: 27382212a99c
Create Date: 2017-01-19 11:36:17.894441
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '459e5ec98b96'
down_revision = '27382212a99c'


def upgrade():
    op.add_column('ip_network_groups',
                  sa.Column('attachment_access_override', sa.Boolean(), nullable=False, server_default='false'),
                  schema='indico')
    op.add_column('ip_network_groups',
                  sa.Column('hidden', sa.Boolean(), nullable=False, server_default='false'),
                  schema='indico')
    op.alter_column('ip_network_groups', 'attachment_access_override', server_default=None, schema='indico')
    op.alter_column('ip_network_groups', 'hidden', server_default=None, schema='indico')


def downgrade():
    op.drop_column('ip_network_groups', 'hidden', schema='indico')
    op.drop_column('ip_network_groups', 'attachment_access_override', schema='indico')
