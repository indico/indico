"""Disallow editing permissions for groups

Revision ID: c0fc1e46888b
Revises: 532f0ea25bb1
Create Date: 2020-06-15 21:42:37.242639
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'c0fc1e46888b'
down_revision = '532f0ea25bb1'
branch_labels = None
depends_on = None


def upgrade():
    permissions = "ARRAY['paper_editing', 'slides_editing', 'poster_editing']"
    condition = 'type NOT IN (2, 3) OR (NOT (permissions::text[] && {}))'.format(permissions)
    op.create_check_constraint('disallow_group_editor_permissions', 'principals', condition, schema='events')


def downgrade():
    op.drop_constraint('ck_principals_disallow_group_editor_permissions', 'principals', schema='events')
