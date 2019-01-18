"""Create ReservationLink model

Revision ID: 416f9c877300
Revises: cbe630695800
Create Date: 2019-01-18 15:14:29.749357
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.links import LinkType


# revision identifiers, used by Alembic.
revision = '416f9c877300'
down_revision = 'ff49d8d05ce7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reservation_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('linked_event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('contribution_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_block_id', sa.Integer(), nullable=True, index=True),
        sa.Column('link_type',
                  PyIntEnum(LinkType, exclude_values={LinkType.category, LinkType.subcontribution, LinkType.session}),
                  nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['linked_event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['session_block_id'], ['events.session_blocks.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='roombooking'
    )

    op.add_column('reservations', sa.Column('link_id', sa.Integer(), nullable=True), schema='roombooking')
    op.create_index(None, 'reservations', ['link_id'], unique=False, schema='roombooking')
    op.create_foreign_key(None, 'reservations', 'reservation_links', ['link_id'], ['id'], source_schema='roombooking',
                          referent_schema='roombooking')


def downgrade():
    op.drop_column('reservations', 'link_id', schema='roombooking')
    op.drop_table('reservation_links', schema='roombooking')
