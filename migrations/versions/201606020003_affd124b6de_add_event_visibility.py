"""Add event visibility

Revision ID: affd124b6de
Revises: 35a6ae289e03
Create Date: 2016-07-14 14:05:24.007841
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'affd124b6de'
down_revision = '35a6ae289e03'


def upgrade():
    op.add_column('events', sa.Column('visibility', sa.Integer(), nullable=True), schema='events')
    op.create_check_constraint('valid_visibility', 'events', "visibility IS NULL OR visibility >= 0", schema='events')


def downgrade():
    op.drop_constraint('ck_events_valid_visibility', 'events', schema='events')
    op.drop_column('events', 'visibility', schema='events')
