"""Add require_privacy_policy_agreement to regforms

Revision ID: a59688f9ba40
Revises: e47fc6634291
Create Date: 2023-05-04 14:05:51.778169
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a59688f9ba40'
down_revision = 'e47fc6634291'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('require_privacy_policy_agreement', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='event_registration')
    op.alter_column('forms', 'require_privacy_policy_agreement', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'require_privacy_policy_agreement', schema='event_registration')
