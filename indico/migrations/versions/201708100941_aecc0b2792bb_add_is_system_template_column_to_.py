"""Add is_system_template column to DesignerTemplate table

Revision ID: aecc0b2792bb
Revises: f6cb3c9cf9ab
Create Date: 2017-08-10 09:41:52.325603
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'aecc0b2792bb'
down_revision = 'f6cb3c9cf9ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('is_system_template', sa.Boolean(), nullable=False,
                                                  server_default='false'), schema='indico')
    op.alter_column('designer_templates', 'is_system_template', server_default=None, schema='indico')


def downgrade():
    op.drop_column('designer_templates', 'is_system_template', schema='indico')
