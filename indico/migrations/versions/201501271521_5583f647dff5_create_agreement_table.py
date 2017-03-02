"""Create agreement table

Revision ID: 5583f647dff5
Revises: 4f11eb4b607b
Create Date: 2015-01-27 15:21:59.489742
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.modules.events.agreements.models.agreements import AgreementState


# revision identifiers, used by Alembic.
revision = '5583f647dff5'
down_revision = '4f11eb4b607b'


def upgrade():
    op.create_table('agreements',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('uuid', sa.String(), nullable=False),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.Column('identifier', sa.String(), nullable=False),
                    sa.Column('person_email', sa.String(), nullable=False),
                    sa.Column('person_name', sa.String(), nullable=False),
                    sa.Column('state', PyIntEnum(AgreementState), nullable=False),
                    sa.Column('timestamp', UTCDateTime, nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('signed_dt', UTCDateTime, nullable=True),
                    sa.Column('signed_from_ip', sa.String(), nullable=True),
                    sa.Column('reason', sa.String(), nullable=True),
                    sa.Column('attachment', sa.LargeBinary(), nullable=True),
                    sa.Column('attachment_filename', sa.String(), nullable=True),
                    sa.Column('data', postgresql.JSON(), nullable=True),
                    sa.UniqueConstraint('event_id', 'type', 'identifier'),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')


def downgrade():
    op.drop_table('agreements', schema='events')
