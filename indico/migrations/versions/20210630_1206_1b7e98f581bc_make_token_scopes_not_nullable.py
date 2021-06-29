"""Make token scopes not nullable

Revision ID: 1b7e98f581bc
Revises: 1f6738730753
Create Date: 2021-06-30 00:54:37.365288
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '1b7e98f581bc'
down_revision = '1f6738730753'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('tokens', 'scopes', nullable=False, schema='oauth')


def downgrade():
    op.alter_column('tokens', 'scopes', nullable=True, schema='oauth')
