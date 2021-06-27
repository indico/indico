"""Add reminder send_to_speakers column

Revision ID: 420195768776
Revises: 90384b9b3d22
Create Date: 2021-06-27 23:17:44.458327
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '420195768776'
down_revision = '90384b9b3d22'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reminders',
                  sa.Column('send_to_speakers', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.alter_column('reminders', 'send_to_speakers', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'send_to_speakers', schema='events')
