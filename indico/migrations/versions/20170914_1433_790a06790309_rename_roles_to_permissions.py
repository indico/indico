"""Rename roles to permissions

Revision ID: 790a06790309
Revises: 640584a3987e
Create Date: 2017-09-14 14:33:27.890171
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '790a06790309'
down_revision = '640584a3987e'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('principals', 'roles', new_column_name='permissions', schema='categories')
    op.alter_column('contribution_principals', 'roles', new_column_name='permissions', schema='events')
    op.alter_column('principals', 'roles', new_column_name='permissions', schema='events')
    op.alter_column('session_principals', 'roles', new_column_name='permissions', schema='events')


def downgrade():
    op.alter_column('principals', 'permissions', new_column_name='roles', schema='categories')
    op.alter_column('contribution_principals', 'permissions', new_column_name='roles', schema='events')
    op.alter_column('principals', 'permissions', new_column_name='roles', schema='events')
    op.alter_column('session_principals', 'permissions', new_column_name='roles', schema='events')
