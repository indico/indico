"""Add system_template column to DesignerTemplate table

Revision ID: b77a68b1829d
Revises: f6cb3c9cf9ab
Create Date: 2017-08-08 13:03:28.347565
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b77a68b1829d'
down_revision = 'f6cb3c9cf9ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('system_template', sa.Boolean(), nullable=True), schema='indico')
    op.alter_column('designer_templates', sa.Column('system_template', sa.Boolean(), nullable=False), schema='indico')


def downgrade():
    op.drop_column('designer_templates', 'system_template', schema='indico')
