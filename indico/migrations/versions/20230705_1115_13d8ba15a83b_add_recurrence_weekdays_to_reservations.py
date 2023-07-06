"""add recurrence_weekdays to reservations

Revision ID: 13d8ba15a83b
Revises: 5d05eda06776
Create Date: 2023-07-05 11:15:22.561512
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '13d8ba15a83b'
down_revision = '5d05eda06776'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservations', sa.Column('recurrence_weekdays', postgresql.ARRAY(sa.String()), nullable=True), schema='roombooking')
    op.create_check_constraint('valid_recurrence_weekdays', 'reservations', "recurrence_weekdays::text[] <@ ARRAY['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']::text[]", schema='roombooking')


def downgrade():
    op.drop_constraint('ck_reservations_valid_recurrence_weekdays', 'reservations', schema='roombooking')
    op.drop_column('reservations', 'recurrence_weekdays', schema='roombooking')
