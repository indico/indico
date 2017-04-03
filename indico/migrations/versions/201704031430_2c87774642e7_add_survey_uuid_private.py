"""Add survey UUID/private

Revision ID: 2c87774642e7
Revises: 6c744b2be8cf
Create Date: 2017-03-07 14:25:54.829777
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '2c87774642e7'
down_revision = '6c744b2be8cf'


def upgrade():
    op.add_column('surveys', sa.Column('private', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_surveys')
    op.alter_column('surveys', 'private', server_default=None, schema='event_surveys')
    op.add_column('surveys', sa.Column('uuid', postgresql.UUID(), nullable=True), schema='event_surveys')
    op.execute('UPDATE event_surveys.surveys SET uuid=md5(random()::text || clock_timestamp()::text)::uuid')
    op.alter_column('surveys', 'uuid', nullable=False, schema='event_surveys')
    op.create_unique_constraint(None, 'surveys', ['uuid'], schema='event_surveys')


def downgrade():
    op.drop_column('surveys', 'uuid', schema='event_surveys')
    op.drop_column('surveys', 'private', schema='event_surveys')
