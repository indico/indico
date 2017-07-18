"""Add is_clonable column in DesignerTemplate

Revision ID: bbe2ac15f488
Revises: 3ca338ed5192
Create Date: 2017-05-24 10:45:23.271275
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'bbe2ac15f488'
down_revision = '3ca338ed5192'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('designer_templates', sa.Column('is_clonable', sa.Boolean(), nullable=False, server_default='true'),
                  schema='indico')
    op.alter_column('designer_templates', 'is_clonable', server_default=None, schema='indico')


def downgrade():
    op.drop_column('designer_templates', 'is_clonable', schema='indico')
