"""Add not_deletable column to DesignerTemplate table

Revision ID: 80b98c1ccc8f
Revises: fd47fc619616
Create Date: 2017-08-01 15:16:23.552553
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '80b98c1ccc8f'
down_revision = 'fd47fc619616'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('not_deletable', sa.Boolean(), nullable=True), schema='indico')


def downgrade():
    op.drop_column('designer_templates', 'not_deletable', schema='indico')
