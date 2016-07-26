"""Delete category_index table

Revision ID: 58de7b79b532
Revises: 4434377c5cdb
Create Date: 2016-06-03 18:02:38.360146
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '58de7b79b532'
down_revision = '4434377c5cdb'


def upgrade():
    op.drop_table('category_index', schema='categories')


def downgrade():
    op.create_table(
        'category_index',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('title_vector', postgresql.TSVECTOR(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index(None, 'title_vector', postgresql_using='gin'),
        schema='categories'
    )
