"""Move api key table to users schema

Revision ID: 26b356f99ad3
Revises: 51f7943e5784
Create Date: 2015-05-03 21:02:28.968139
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '26b356f99ad3'
down_revision = '51f7943e5784'


def upgrade():
    op.execute('ALTER TABLE indico.api_keys SET SCHEMA users')


def downgrade():
    op.execute('ALTER TABLE users.api_keys SET SCHEMA indico')
