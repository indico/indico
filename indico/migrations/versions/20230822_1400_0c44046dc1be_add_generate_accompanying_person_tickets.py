"""Add generate accompanying person tickets

Revision ID: 0c44046dc1be
Revises: cd7038a37646
Create Date: 2023-08-17 14:12:32.880804
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0c44046dc1be'
down_revision = 'cd7038a37646'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('tickets_for_accompanying_persons', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.alter_column('forms', 'tickets_for_accompanying_persons', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'tickets_for_accompanying_persons', schema='event_registration')
