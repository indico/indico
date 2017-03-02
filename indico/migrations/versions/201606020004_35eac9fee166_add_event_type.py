"""Add event type

Revision ID: 35eac9fee166
Revises: affd124b6de
Create Date: 2016-07-04 17:15:20.292801
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.models.events import EventType


# revision identifiers, used by Alembic.
revision = '35eac9fee166'
down_revision = 'affd124b6de'


def upgrade():
    op.add_column('events', sa.Column('type', PyIntEnum(EventType), nullable=False,
                                      server_default=str(EventType.meeting.value)),
                  schema='events')
    op.alter_column('events', 'type', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'type', schema='events')
