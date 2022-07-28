"""Add category title/description i18n

Revision ID: 7c99d8f13df7
Revises: 33c3ab67d729
Create Date: 2022-06-30 12:06:05.586959
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = '7c99d8f13df7'
down_revision = '33c3ab67d729'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('title_translations', pg.JSONB(), nullable=False, server_default='{}'),
                  schema='categories')
    op.alter_column('categories', 'title_translations', server_default=None, schema='categories')
    op.add_column('categories', sa.Column('description_translations', pg.JSONB(), nullable=False, server_default='{}'),
                  schema='categories')
    op.alter_column('categories', 'description_translations', server_default=None, schema='categories')


def downgrade():
    op.drop_column('categories', 'description_translations', schema='categories')
    op.drop_column('categories', 'title_translations', schema='categories')
