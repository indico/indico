"""Add generate accompanying person tickets

Revision ID: 0c44046dc1be
Revises: b45847c0e62f
Create Date: 2022-08-30 14:28:32.880804
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0c44046dc1be'
down_revision = 'b45847c0e62f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('tickets_for_accompanying_persons', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.alter_column('forms', 'tickets_for_accompanying_persons', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'tickets_for_accompanying_persons', schema='event_registration')
