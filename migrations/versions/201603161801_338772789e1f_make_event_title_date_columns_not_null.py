"""Make event title/date columns not null

Revision ID: 338772789e1f
Revises: ae00a6a1edd
Create Date: 2016-02-24 14:21:29.617383
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '338772789e1f'
down_revision = 'ae00a6a1edd'


def upgrade():
    op.alter_column('events', 'start_dt', nullable=False, schema='events')
    op.alter_column('events', 'end_dt', nullable=False, schema='events')
    op.alter_column('events', 'timezone', nullable=False, schema='events')
    op.alter_column('events', 'title', nullable=False, schema='events')
    op.alter_column('events', 'description', nullable=False, schema='events')


def downgrade():
    op.alter_column('events', 'description', nullable=True, schema='events')
    op.alter_column('events', 'title', nullable=True, schema='events')
    op.alter_column('events', 'timezone', nullable=True, schema='events')
    op.alter_column('events', 'end_dt', nullable=True, schema='events')
    op.alter_column('events', 'start_dt', nullable=True, schema='events')
