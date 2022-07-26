"""Add require_captcha to regforms

Revision ID: b60f5c45acf7
Revises: 0c4bb2973536
Create Date: 2022-07-27 10:07:49.004290
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b60f5c45acf7'
down_revision = '33c3ab67d729'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('require_captcha', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('forms', 'require_captcha', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'require_captcha', schema='event_registration')
