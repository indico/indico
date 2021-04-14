"""Make OAuth PKCE flow configurable

Revision ID: c36abe1c23c7
Revises: da06d8f50342
Create Date: 2021-02-22 17:54:16.270477
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c36abe1c23c7'
down_revision = 'da06d8f50342'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('applications', sa.Column('allow_pkce_flow', sa.Boolean(), server_default='false', nullable=False),
                  schema='oauth')
    op.execute('UPDATE oauth.applications SET allow_pkce_flow = true WHERE system_app_type = 1')
    op.alter_column('applications', 'allow_pkce_flow', server_default=None, schema='oauth')


def downgrade():
    op.drop_column('applications', 'allow_pkce_flow', schema='oauth')
