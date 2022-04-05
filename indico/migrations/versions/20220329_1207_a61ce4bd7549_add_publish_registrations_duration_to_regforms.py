"""Add publish registrations duration to registration forms

Revision ID: a61ce4bd7549
Revises: 57696d76f9b0
Create Date: 2022-03-29 12:07:54.108451
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a61ce4bd7549'
down_revision = '57696d76f9b0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms',
                  sa.Column('publish_registrations_duration', sa.Interval(), nullable=True),
                  schema='event_registration')


def downgrade():
    op.drop_column('forms', 'publish_registrations_duration', schema='event_registration')
