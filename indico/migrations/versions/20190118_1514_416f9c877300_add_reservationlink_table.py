"""Add reservation link table

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
        sa.CheckConstraint('(event_id IS NULL) = (link_type = 1)', name='valid_event_id'),
        sa.CheckConstraint('link_type != 2 OR (contribution_id IS NULL AND session_block_id IS NULL AND '
                           'linked_event_id IS NOT NULL)', name='valid_event_link'),
        sa.CheckConstraint('link_type != 3 OR (linked_event_id IS NULL AND session_block_id IS NULL AND '
                           'contribution_id IS NOT NULL)', name='valid_contribution_link'),
        sa.CheckConstraint('link_type != 6 OR (contribution_id IS NULL AND linked_event_id IS NULL AND '
                           'session_block_id IS NOT NULL)', name='valid_session_block_link'),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['linked_event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['session_block_id'], ['events.session_blocks.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='roombooking'
    )

    op.add_column('reservations', sa.Column('link_id', sa.Integer(), nullable=True, index=True), schema='roombooking')
    op.create_foreign_key(None, 'reservations', 'reservation_links', ['link_id'], ['id'], source_schema='roombooking',
                          referent_schema='roombooking')

    # Migrate reservations.event_id to new reservation_links and set
    # reservations.link_id based on the id of the newly created row.
    op.execute('''
        WITH reserv_data AS (
            SELECT nextval(pg_get_serial_sequence('roombooking.reservation_links', 'id')) AS new_link_id,
            id AS reserv_id, event_id
            FROM roombooking.reservations
            WHERE event_id IS NOT NULL
        ), link_ids_data AS (
            INSERT INTO roombooking.reservation_links (id, event_id, linked_event_id, link_type)
            SELECT new_link_id, event_id, event_id, {}
            FROM reserv_data
            RETURNING id AS link_id
        )
        UPDATE roombooking.reservations
        SET link_id = link_ids_data.link_id
        FROM link_ids_data, reserv_data
        WHERE id = reserv_data.reserv_id and link_ids_data.link_id = reserv_data.new_link_id;
    '''.format(LinkType.event.value))

    op.drop_column('reservations', 'event_id', schema='roombooking')


def downgrade():
    op.add_column('reservations', sa.Column('event_id', sa.Integer(), nullable=True), schema='roombooking')
    op.create_foreign_key(None, 'reservations', 'events', ['event_id'], ['id'], source_schema='roombooking',
                          referent_schema='events')
    op.create_index(None, 'reservations', ['event_id'], unique=False, schema='roombooking')

    # Move reservation_links.event_id back to reservation.event_id
    op.execute('''
        UPDATE roombooking.reservations
        SET event_id = reserv_link.event_id
        FROM (
            SELECT id, event_id
            FROM roombooking.reservation_links
            WHERE event_id IS NOT NULL
        ) reserv_link
        WHERE link_id = reserv_link.id;
    ''')

    op.drop_column('reservations', 'link_id', schema='roombooking')
    op.drop_table('reservation_links', schema='roombooking')
