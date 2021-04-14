"""Rename oauth default_scopes

Revision ID: 3782de7970da
Revises: f26c201c8254
Create Date: 2021-02-19 14:28:23.469730
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3782de7970da'
down_revision = 'f26c201c8254'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('applications', 'default_scopes', new_column_name='allowed_scopes', schema='oauth')


def downgrade():
    op.alter_column('applications', 'allowed_scopes', new_column_name='default_scopes', schema='oauth')
