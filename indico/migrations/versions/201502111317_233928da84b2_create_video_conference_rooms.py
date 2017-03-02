"""Create videoconference rooms

Revision ID: 233928da84b2
Revises: 50c2b5ee2726
Create Date: 2015-02-11 13:17:44.365589
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.modules.vc.models.vc_rooms import VCRoomLinkType, VCRoomStatus
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '233928da84b2'
down_revision = '5583f647dff5'


def upgrade():
    op.create_table('vc_rooms',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('status', PyIntEnum(VCRoomStatus), nullable=False),
                    sa.Column('created_by_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.Column('modified_dt', UTCDateTime, nullable=True),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')
    op.create_table('vc_room_events',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
                    sa.Column('vc_room_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('link_type', PyIntEnum(VCRoomLinkType), nullable=False),
                    sa.Column('link_id', sa.String(), nullable=True),
                    sa.Column('show', sa.Boolean(), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.ForeignKeyConstraint(['vc_room_id'], ['events.vc_rooms.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')


def downgrade():
    op.drop_table('vc_room_events', schema='events')
    op.drop_table('vc_rooms', schema='events')
