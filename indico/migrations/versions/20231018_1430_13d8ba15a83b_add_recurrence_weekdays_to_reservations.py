"""Add recurrence_weekdays to reservations

Revision ID: 13d8ba15a83b
Revises: d8562ad31e90
Create Date: 2023-10-18 14:30:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '13d8ba15a83b'
down_revision = 'd8562ad31e90'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservations', sa.Column('recurrence_weekdays', postgresql.ARRAY(sa.String()), nullable=True),
                  schema='roombooking')
    op.create_check_constraint(
        'valid_recurrence_weekdays', 'reservations',
        "recurrence_weekdays::text[] <@ ARRAY['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']::text[]",
        schema='roombooking'
    )


def downgrade():
    op.drop_column('reservations', 'recurrence_weekdays', schema='roombooking')
