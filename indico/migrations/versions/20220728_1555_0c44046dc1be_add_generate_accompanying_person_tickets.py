"""Add generate accompanying person tickets

Revision ID: 0c44046dc1be
Revises: b60f5c45acf7
Create Date: 2022-07-28 15:55:32.880804
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0c44046dc1be'
down_revision = 'b60f5c45acf7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('tickets_for_accompanying_persons', sa.Boolean(), nullable=False,
                                     server_default='true'), schema='event_registration')
    op.alter_column('forms', 'tickets_for_accompanying_persons', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'tickets_for_accompanying_persons', schema='event_registration')
