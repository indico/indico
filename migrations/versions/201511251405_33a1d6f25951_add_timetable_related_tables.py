"""Add timetable related tables

Revision ID: 33a1d6f25951
Revises: 225d0750c216
Create Date: 2015-11-25 14:05:51.856236
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.timetable.models.entries import TimetableEntryType


# revision identifiers, used by Alembic.
revision = '33a1d6f25951'
down_revision = '225d0750c216'


def upgrade():
    # Break
    op.create_table(
        'breaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('duration', sa.Interval(), nullable=False),
        sa.Column('text_color', sa.String(), nullable=False),
        sa.Column('background_color', sa.String(), nullable=False),
        sa.Column('room_name', sa.String(), nullable=False),
        sa.Column('inherit_location', sa.Boolean(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=True, index=True),
        sa.Column('venue_name', sa.String(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                           name='no_custom_location_if_room'),
        sa.CheckConstraint("(venue_id IS NULL) OR (venue_name = '')", name='no_venue_name_if_venue_id'),
        sa.CheckConstraint("(room_id IS NULL) OR (venue_id IS NOT NULL)", name='venue_id_if_room_id'),
        sa.CheckConstraint("NOT inherit_location OR (venue_id IS NULL AND room_id IS NULL AND venue_name = '' AND "
                           "room_name = '' AND address = '')", name='inherited_location'),
        sa.CheckConstraint("(text_color = '') = (background_color = '')", name='both_or_no_colors'),
        sa.CheckConstraint("text_color != '' AND background_color != ''", name='colors_not_empty'),
        sa.ForeignKeyConstraint(['room_id'], ['roombooking.rooms.id']),
        sa.ForeignKeyConstraint(['venue_id'], ['roombooking.locations.id']),
        sa.ForeignKeyConstraint(['venue_id', 'room_id'], ['roombooking.rooms.location_id', 'roombooking.rooms.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )

    # TimetableEntry
    op.create_table(
        'timetable_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('parent_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_block_id', sa.Integer(), nullable=True, index=True, unique=True),
        sa.Column('contribution_id', sa.Integer(), nullable=True, index=True, unique=True),
        sa.Column('break_id', sa.Integer(), nullable=True, index=True, unique=True),
        sa.Column('type', PyIntEnum(TimetableEntryType), nullable=False),
        sa.Column('start_dt', UTCDateTime, nullable=False),
        sa.Index('ix_timetable_entries_start_dt_desc', sa.text('start_dt DESC')),
        sa.CheckConstraint('type != 1 OR parent_id IS NULL', name='valid_parent'),
        sa.CheckConstraint('type != 1 OR (contribution_id IS NULL AND break_id IS NULL AND '
                           'session_block_id IS NOT NULL)', name='valid_session_block'),
        sa.CheckConstraint('type != 2 OR (session_block_id IS NULL AND break_id IS NULL AND '
                           'contribution_id IS NOT NULL)', name='valid_contribution'),
        sa.CheckConstraint('type != 3 OR (contribution_id IS NULL AND session_block_id IS NULL AND '
                           'break_id IS NOT NULL)', name='valid_break'),
        sa.ForeignKeyConstraint(['break_id'], ['events.breaks.id']),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['events.timetable_entries.id']),
        sa.ForeignKeyConstraint(['session_block_id'], ['events.session_blocks.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )


def downgrade():
    op.drop_table('timetable_entries', schema='events')
    op.drop_table('breaks', schema='events')
