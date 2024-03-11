"""Link events to reservation occurrences

Revision ID: b37cbc4bb129
Revises: e4ac92d27295
Create Date: 2023-12-22 14:08:45.669303
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b37cbc4bb129'
down_revision = 'e4ac92d27295'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('reservation_links', 'reservation_occurrence_links', schema='roombooking')
    op.add_column('reservation_occurrences', sa.Column('link_id', sa.Integer(), nullable=True), schema='roombooking')
    op.create_foreign_key(None, 'reservation_occurrences', 'reservation_occurrence_links', ['link_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')
    op.create_index(None, 'reservation_occurrences', ['link_id'], schema='roombooking')

    op.execute('''
        UPDATE roombooking.reservation_occurrences
        SET link_id = reservations.link_id
        FROM roombooking.reservations
        WHERE
            roombooking.reservation_occurrences.reservation_id = reservations.id AND
            roombooking.reservation_occurrences.start_dt = reservations.start_dt AND
            reservations.link_id IS NOT NULL;
    ''')

    op.execute('''
        ALTER SEQUENCE roombooking.reservation_links_id_seq RENAME TO reservation_occurrence_links_id_seq;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT pk_reservation_links TO pk_reservation_occurrence_links;
        ALTER INDEX roombooking.ix_reservation_links_contribution_id RENAME TO ix_reservation_occurrence_links_contribution_id;
        ALTER INDEX roombooking.ix_reservation_links_event_id RENAME TO ix_reservation_occurrence_links_event_id;
        ALTER INDEX roombooking.ix_reservation_links_linked_event_id RENAME TO ix_reservation_occurrence_links_linked_event_id;
        ALTER INDEX roombooking.ix_reservation_links_session_block_id RENAME TO ix_reservation_occurrence_links_session_block_id;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT ck_reservation_links_valid_contribution_link TO ck_reservation_occurrence_links_valid_contribution_link;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT ck_reservation_links_valid_enum_link_type TO ck_reservation_occurrence_links_valid_enum_link_type;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT ck_reservation_links_valid_event_id TO ck_reservation_occurrence_links_valid_event_id;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT ck_reservation_links_valid_event_link TO ck_reservation_occurrence_links_valid_event_link;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT ck_reservation_links_valid_session_block_link TO ck_reservation_occurrence_links_valid_session_block_link;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT fk_reservation_links_contribution_id_contributions TO fk_reservation_occurrence_links_contribution_id_contributions;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT fk_reservation_links_event_id_events TO fk_reservation_occurrence_links_event_id_events;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT fk_reservation_links_linked_event_id_events TO fk_reservation_occurrence_links_linked_event_id_events;
        ALTER TABLE roombooking.reservation_occurrence_links RENAME CONSTRAINT fk_reservation_links_session_block_id_session_blocks TO fk_reservation_occurrence_links_session_block_id_session_blocks;
    ''')

    op.drop_column('reservations', 'link_id', schema='roombooking')


def downgrade():
    op.rename_table('reservation_occurrence_links', 'reservation_links', schema='roombooking')
    op.add_column('reservations', sa.Column('link_id', sa.Integer(), nullable=True), schema='roombooking')
    op.create_foreign_key(None, 'reservations', 'reservation_links', ['link_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')

    op.execute('''
        UPDATE roombooking.reservations
        SET link_id = reservation_occurrences.link_id
        FROM roombooking.reservation_occurrences
        WHERE
            roombooking.reservation_occurrences.reservation_id = reservations.id AND
            roombooking.reservation_occurrences.start_dt = reservations.start_dt AND
            roombooking.reservation_occurrences.link_id IS NOT NULL;
    ''')

    op.execute('''
        ALTER SEQUENCE roombooking.reservation_occurrence_links_id_seq RENAME TO reservation_links_id_seq;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT pk_reservation_occurrence_links TO pk_reservation_links;
        ALTER INDEX roombooking.ix_reservation_occurrence_links_contribution_id RENAME TO ix_reservation_links_contribution_id;
        ALTER INDEX roombooking.ix_reservation_occurrence_links_event_id RENAME TO ix_reservation_links_event_id;
        ALTER INDEX roombooking.ix_reservation_occurrence_links_linked_event_id RENAME TO ix_reservation_links_linked_event_id;
        ALTER INDEX roombooking.ix_reservation_occurrence_links_session_block_id RENAME TO ix_reservation_links_session_block_id;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT ck_reservation_occurrence_links_valid_contribution_link TO ck_reservation_links_valid_contribution_link;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT ck_reservation_occurrence_links_valid_enum_link_type TO ck_reservation_links_valid_enum_link_type;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT ck_reservation_occurrence_links_valid_event_id TO ck_reservation_links_valid_event_id;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT ck_reservation_occurrence_links_valid_event_link TO ck_reservation_links_valid_event_link;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT ck_reservation_occurrence_links_valid_session_block_link TO ck_reservation_links_valid_session_block_link;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT fk_reservation_occurrence_links_contribution_id_contributions TO fk_reservation_links_contribution_id_contributions;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT fk_reservation_occurrence_links_event_id_events TO fk_reservation_links_event_id_events;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT fk_reservation_occurrence_links_linked_event_id_events TO fk_reservation_links_linked_event_id_events;
        ALTER TABLE roombooking.reservation_links RENAME CONSTRAINT fk_reservation_occurrence_links_session_block_id_session_blocks TO fk_reservation_links_session_block_id_session_blocks;
    ''')

    op.drop_column('reservation_occurrences', 'link_id', schema='roombooking')
