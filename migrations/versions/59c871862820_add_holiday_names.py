"""Add holiday names

Revision ID: 59c871862820
Revises: 3f9eb90460f3
Create Date: 2014-08-06 13:37:49.560665
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59c871862820'
down_revision = '3f9eb90460f3'


def upgrade():
    upgrade_schema()


def downgrade():
    downgrade_schema()


def upgrade_schema():
    op.add_column('holidays', sa.Column('name', sa.String(), nullable=True))


def downgrade_schema():
    op.drop_column('holidays', 'name')
