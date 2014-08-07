"""Rename is_confirmed to is_accepted

Revision ID: 2dcc90572846
Revises: 59c871862820
Create Date: 2014-08-07 14:37:16.250441
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2dcc90572846'
down_revision = '59c871862820'


def upgrade():
    upgrade_schema()


def downgrade():
    downgrade_schema()


def upgrade_schema():
    op.alter_column('reservations', 'is_confirmed', new_column_name='is_accepted')


def downgrade_schema():
    op.alter_column('reservations', 'is_accepted', new_column_name='is_confirmed')
