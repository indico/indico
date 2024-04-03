"""Add Apple Pass integration

Revision ID: 16c9445951f4
Revises: 492c6d801a4a
Create Date: 2024-02-27 13:39:03.735267
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '16c9445951f4'
down_revision = '492c6d801a4a'
branch_labels = None
depends_on = None


class _InheritableConfigMode(int, Enum):
    disabled = 0
    enabled = 1
    inheriting = 2


def upgrade():
    op.add_column('categories', sa.Column('apple_pass_mode', PyIntEnum(_InheritableConfigMode), nullable=False,
                                          server_default=str(_InheritableConfigMode.inheriting.value)),
                  schema='categories')
    op.add_column('categories', sa.Column('apple_pass_settings', postgresql.JSONB(), nullable=False,
                                          server_default='{}'), schema='categories')
    op.add_column('forms', sa.Column('ticket_apple_pass', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    # This will be needed for the implementation of Apple Pass updates
    op.add_column('registrations', sa.Column('apple_pass_serial', sa.String(), server_default='', nullable=False),
                  schema='event_registration')
    op.alter_column('forms', 'ticket_apple_pass', server_default=None, schema='event_registration')
    op.alter_column('categories', 'apple_pass_mode', server_default=None, schema='categories')
    op.alter_column('categories', 'apple_pass_settings', server_default=None, schema='categories')
    op.alter_column('registrations', 'apple_pass_serial', server_default=None, schema='event_registration')
    op.execute(f'''
        UPDATE categories.categories
        SET apple_pass_mode = {_InheritableConfigMode.disabled.value}
        WHERE parent_id IS NULL
    ''')  # noqa: S608
    op.create_check_constraint('root_not_inheriting_ap_mode', 'categories',
                               f'(id != 0) OR (apple_pass_mode != {_InheritableConfigMode.inheriting.value})',
                               schema='categories')
    op.create_check_constraint('ap_configured_if_enabled', 'categories',
                               f'(apple_pass_mode != {_InheritableConfigMode.enabled.value}) OR '
                               "(apple_pass_settings != '{}'::jsonb)",
                               schema='categories')


def downgrade():
    op.drop_column('forms', 'ticket_apple_pass', schema='event_registration')
    op.drop_column('categories', 'apple_pass_settings', schema='categories')
    op.drop_column('categories', 'apple_pass_mode', schema='categories')
    op.drop_column('registrations', 'apple_pass_serial', schema='event_registration')
