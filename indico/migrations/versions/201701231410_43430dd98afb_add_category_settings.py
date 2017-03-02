"""Add category settings

Revision ID: 43430dd98afb
Revises: 1f443d77da5d
Create Date: 2017-01-23 14:10:57.844378
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '43430dd98afb'
down_revision = '1f443d77da5d'


def upgrade():
    op.create_table('settings',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('module', sa.String(), nullable=False, index=True),
                    sa.Column('name', sa.String(), nullable=False, index=True),
                    sa.Column('value', postgresql.JSON(), nullable=False),
                    sa.Column('category_id', sa.Integer(), nullable=False, index=True),
                    sa.ForeignKeyConstraint(['category_id'], [u'categories.categories.id']),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('category_id', 'module', 'name'),
                    sa.CheckConstraint('module = lower(module)', 'lowercase_module'),
                    sa.CheckConstraint('name = lower(name)', 'lowercase_name'),
                    sa.Index(None, 'category_id', 'module', unique=False),
                    sa.Index(None, 'category_id', 'module', 'name', unique=False),
                    schema='categories')


def downgrade():
    op.drop_table('settings', schema='categories')
