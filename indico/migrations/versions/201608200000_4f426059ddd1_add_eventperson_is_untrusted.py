"""Add EventPerson.is_untrusted

Revision ID: 4f426059ddd1
Revises: ccd9d0858ff
Create Date: 2016-11-23 16:45:37.646802
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '4f426059ddd1'
down_revision = 'ccd9d0858ff'


def upgrade():
    op.add_column('persons', sa.Column('is_untrusted', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.alter_column('persons', 'is_untrusted', server_default=None, schema='events')


def downgrade():
    op.drop_column('persons', 'is_untrusted', schema='events')
