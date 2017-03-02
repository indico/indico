"""Make settings columns NOT NULL

Revision ID: 48084f0df78c
Revises: 57d33a15626a
Create Date: 2014-11-24 13:40:53.665826
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '48084f0df78c'
down_revision = '57d33a15626a'


def upgrade():
    op.alter_column('settings', 'module', nullable=False, schema='indico')
    op.alter_column('settings', 'name', nullable=False, schema='indico')
    op.alter_column('settings', 'value', nullable=False, schema='indico')


def downgrade():
    op.alter_column('settings', 'value', nullable=True, schema='indico')
    op.alter_column('settings', 'name', nullable=True, schema='indico')
    op.alter_column('settings', 'module', nullable=True, schema='indico')
