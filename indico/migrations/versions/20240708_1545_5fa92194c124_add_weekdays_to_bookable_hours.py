"""Add weekdays to bookable hours

Revision ID: 5fa92194c124
Revises: 85f58503310c
Create Date: 2024-07-08 15:45:50.791351
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '5fa92194c124'
down_revision = '85f58503310c'
branch_labels = None
depends_on = None


def upgrade():
    # we can't specify the `serial` type w/o SQL or a custom type definition...
    op.execute('ALTER TABLE roombooking.room_bookable_hours ADD COLUMN id SERIAL')
    op.add_column('room_bookable_hours', sa.Column('weekday', sa.String(), nullable=True), schema='roombooking')
    op.drop_constraint('pk_room_bookable_hours', 'room_bookable_hours', schema='roombooking')
    op.create_primary_key(None, 'room_bookable_hours', ['id'], schema='roombooking')
    op.create_check_constraint(
        'valid_weekdays', 'room_bookable_hours',
        "weekday::text IN ('mon'::text, 'tue'::text, 'wed'::text, 'thu'::text, 'fri'::text, 'sat'::text, 'sun'::text)",
        schema='roombooking'
    )
    op.create_index(None, 'room_bookable_hours', ['room_id', 'start_time', 'end_time', 'weekday'], unique=True,
                    schema='roombooking')


def downgrade():
    op.drop_column('room_bookable_hours', 'weekday', schema='roombooking')
    op.drop_column('room_bookable_hours', 'id', schema='roombooking')
    op.create_primary_key(None, 'room_bookable_hours', ['start_time', 'end_time', 'room_id'], schema='roombooking')
