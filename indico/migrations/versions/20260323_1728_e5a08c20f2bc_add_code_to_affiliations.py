"""Add code to affiliations

Revision ID: e5a08c20f2bc
Revises: af9d03d7073c
Create Date: 2026-03-23 17:28:10.101572
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e5a08c20f2bc'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('affiliations', sa.Column('code', sa.String(), nullable=False, server_default=''), schema='indico')
    op.alter_column('affiliations', 'code', server_default=None, schema='indico')


def downgrade():
    op.drop_column('affiliations', 'code', schema='indico')
