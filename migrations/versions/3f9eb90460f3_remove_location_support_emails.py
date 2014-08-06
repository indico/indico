"""Remove location support emails

Revision ID: 3f9eb90460f3
Revises: 46c709d457cc
Create Date: 2014-08-06 10:27:57.121646
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f9eb90460f3'
down_revision = '46c709d457cc'


def upgrade():
    upgrade_schema()


def downgrade():
    downgrade_schema()


def upgrade_schema():
    op.drop_column('locations', 'support_emails')


def downgrade_schema():
    op.add_column('locations', sa.Column('support_emails', sa.VARCHAR(), autoincrement=False, nullable=True))
