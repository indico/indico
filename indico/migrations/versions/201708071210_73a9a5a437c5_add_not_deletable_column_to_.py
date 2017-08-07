"""Add not_deletable column to DesignerTemplate table

Revision ID: 73a9a5a437c5
Revises: f6cb3c9cf9ab
Create Date: 2017-08-07 12:10:02.985975
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '73a9a5a437c5'
down_revision = 'f6cb3c9cf9ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('not_deletable', sa.Boolean(), nullable=True), schema='indico')
    op.alter_column('designer_templates', sa.Column('not_deletable', sa.Boolean(), nullable=False), schema='indico')


def downgrade():
    op.drop_column('designer_templates', 'not_deletable', schema='indico')
