"""Link events to reservation occurrences.

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

    op.execute('''
        UPDATE roombooking.reservation_occurrences
        SET link_id = reservations.link_id
        FROM roombooking.reservations
        WHERE
            roombooking.reservation_occurrences.reservation_id = reservations.id AND
            roombooking.reservation_occurrences.start_dt = reservations.start_dt AND
            reservations.link_id IS NOT NULL;
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

    op.drop_column('reservation_occurrences', 'link_id', schema='roombooking')
