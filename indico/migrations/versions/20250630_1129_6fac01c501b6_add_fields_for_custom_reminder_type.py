"""Add fields for custom reminder type

Revision ID: 6fac01c501b6
Revises: f2518f111aa7
Create Date: 2025-05-14 11:29:31.975949
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '6fac01c501b6'
down_revision = 'f2518f111aa7'
branch_labels = None
depends_on = None


class _ReminderType(int, Enum):
    classic = 1
    custom = 2


def upgrade():
    op.add_column('reminders',
                  sa.Column('subject', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.alter_column('reminders', 'subject', server_default=None, schema='events')
    op.add_column('reminders',
                  sa.Column('reminder_type', PyIntEnum(_ReminderType), nullable=False, server_default='1'),
                  schema='events')
    op.alter_column('reminders', 'reminder_type', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'reminder_type', schema='events')
    op.drop_column('reminders', 'subject', schema='events')
