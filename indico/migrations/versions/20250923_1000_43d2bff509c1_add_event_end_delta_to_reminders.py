"""Add event_end_delta to event reminders

Revision ID: 43d2bff509c1
Revises: 869fb2760b41
Create Date: 2025-09-23 10:00:03.291861
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '43d2bff509c1'
down_revision = '869fb2760b41'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reminders', sa.Column('event_end_delta', sa.Interval(), nullable=True), schema='events')
    op.create_check_constraint(
        'event_start_delta_or_end_delta_is_null',
        'reminders',
        '(event_start_delta IS NULL) OR (event_end_delta IS NULL)',
        schema='events'
    )


def downgrade():
    op.drop_constraint('ck_reminders_event_start_delta_or_end_delta_is_null', 'reminders', schema='events')
    op.drop_column('reminders', 'event_end_delta', schema='events')
