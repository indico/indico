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


SQL_FUNCTION_ARRAY_IS_UNIQUE = '''
    CREATE FUNCTION indico.array_is_unique(value text[])
        RETURNS boolean
    AS $$
        SELECT COALESCE(COUNT(DISTINCT a) = array_length(value, 1), true)
        FROM unnest(value) a
    $$
    LANGUAGE SQL IMMUTABLE STRICT;
'''


def upgrade():
    op.execute(SQL_FUNCTION_ARRAY_IS_UNIQUE)
    op.add_column('reservations', sa.Column('recurrence_weekdays', postgresql.ARRAY(sa.String()), nullable=True),
                  schema='roombooking')
    op.create_check_constraint(
        'valid_recurrence_weekdays', 'reservations',
        "indico.array_is_unique(recurrence_weekdays) AND recurrence_weekdays::text[] <@ ARRAY['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']::text[]",
        schema='roombooking'
    )
    op.create_check_constraint(
        'recurrence_weekdays_only_weekly', 'reservations', '(recurrence_weekdays IS NULL) OR repeat_frequency = 2',
        schema='roombooking'
    )


def downgrade():
    op.drop_column('reservations', 'recurrence_weekdays', schema='roombooking')
    op.execute('DROP FUNCTION indico.array_is_unique(value text[])')
