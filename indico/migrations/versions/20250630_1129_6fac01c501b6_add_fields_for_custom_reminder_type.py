"""Add fields for custom reminder type

Revision ID: 6fac01c501b6
Revises: b4ee48f3052c
Create Date: 2025-05-14 11:29:31.975949
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '6fac01c501b6'
down_revision = 'b4ee48f3052c'
branch_labels = None
depends_on = None


class _ReminderType(int, Enum):
    standard = 1
    custom = 2


class _RenderMode(int, Enum):
    html = 1
    markdown = 2
    plain_text = 3


def upgrade():
    op.alter_column('reminders', 'message', type_=sa.Text(), schema='events')
    op.add_column('reminders', sa.Column('render_mode', PyIntEnum(_RenderMode), nullable=False, server_default='3'),
                  schema='events')
    op.alter_column('reminders', 'render_mode', server_default=None, schema='events')
    op.add_column('reminders', sa.Column('subject', sa.String(), nullable=False, server_default=''), schema='events')
    op.alter_column('reminders', 'subject', server_default=None, schema='events')
    op.add_column('reminders', sa.Column('reminder_type', PyIntEnum(_ReminderType), nullable=False, server_default='1'),
                  schema='events')
    op.alter_column('reminders', 'reminder_type', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'reminder_type', schema='events')
    op.drop_column('reminders', 'subject', schema='events')
    op.drop_column('reminders', 'render_mode', schema='events')
    op.alter_column('reminders', 'message', type_=sa.String(), schema='events')
