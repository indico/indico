"""Create static sites table

Revision ID: 4e27c1f90362
Revises: 222b9d8d4e22
Create Date: 2015-05-21 13:58:06.566703
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.static.models.static import StaticSiteState


# revision identifiers, used by Alembic.
revision = '4e27c1f90362'
down_revision = '222b9d8d4e22'


def upgrade():
    op.create_table('static_sites',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.Column('state', PyIntEnum(StaticSiteState), nullable=False),
                    sa.Column('requested_dt', UTCDateTime, nullable=False),
                    sa.Column('path', sa.String(), nullable=True),
                    sa.Column('creator_id', sa.Integer(), index=True, nullable=False),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')


def downgrade():
    op.drop_table('static_sites', schema='events')
