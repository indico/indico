"""Add Google Wallet integration

Revision ID: 492c6d801a4a
Revises: 0acf26d68434
Create Date: 2023-11-07 09:56:13.034271
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '492c6d801a4a'
down_revision = '0acf26d68434'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('ticket_google_wallet_enabled', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.add_column('categories', sa.Column('google_wallet_settings', postgresql.JSONB(), nullable=False,
                                          server_default='{}'), schema='categories')
    op.alter_column('forms', 'ticket_google_wallet_enabled', server_default=None, schema='event_registration')
    op.alter_column('categories', 'google_wallet_settings', server_default=None, schema='categories')


def downgrade():
    op.drop_column('forms', 'ticket_google_wallet_enabled', schema='event_registration')
    op.drop_column('categories', 'google_wallet_settings', schema='categories')
