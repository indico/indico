"""Add Google Wallet integration

Revision ID: 492c6d801a4a
Revises: 17996ef18cb9
Create Date: 2024-02-19 09:56:13.034271
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = '492c6d801a4a'
down_revision = '17996ef18cb9'
branch_labels = None
depends_on = None


class _InheritableConfigMode(int, Enum):
    disabled = 0
    enabled = 1
    inheriting = 2


def upgrade():
    op.add_column('forms', sa.Column('ticket_google_wallet', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.add_column('categories', sa.Column('google_wallet_mode', PyIntEnum(_InheritableConfigMode), nullable=False,
                                          server_default=str(_InheritableConfigMode.inheriting.value)),
                  schema='categories')
    op.add_column('categories', sa.Column('google_wallet_settings', postgresql.JSONB(), nullable=False,
                                          server_default='{}'), schema='categories')
    op.alter_column('forms', 'ticket_google_wallet', server_default=None, schema='event_registration')
    op.alter_column('categories', 'google_wallet_mode', server_default=None, schema='categories')
    op.alter_column('categories', 'google_wallet_settings', server_default=None, schema='categories')
    op.execute(f'''
        UPDATE categories.categories
        SET google_wallet_mode = {_InheritableConfigMode.disabled.value}
        WHERE parent_id IS NULL
    ''')  # noqa: S608
    op.create_check_constraint('root_not_inheriting_gw_mode', 'categories',
                               f'(id != 0) OR (google_wallet_mode != {_InheritableConfigMode.inheriting.value})',
                               schema='categories')
    op.create_check_constraint('gw_configured_if_enabled', 'categories',
                               f'(google_wallet_mode != {_InheritableConfigMode.enabled.value}) OR '
                               "(google_wallet_settings != '{}'::jsonb)",
                               schema='categories')


def downgrade():
    op.drop_column('forms', 'ticket_google_wallet', schema='event_registration')
    op.drop_column('categories', 'google_wallet_settings', schema='categories')
    op.drop_column('categories', 'google_wallet_mode', schema='categories')
