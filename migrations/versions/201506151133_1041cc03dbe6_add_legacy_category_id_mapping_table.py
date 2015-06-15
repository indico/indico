"""Add legacy category id mapping table

Revision ID: 1041cc03dbe6
Revises: 513886dc5547
Create Date: 2015-06-15 11:33:33.472399
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

# revision identifiers, used by Alembic.
revision = '1041cc03dbe6'
down_revision = '513886dc5547'


def upgrade():
    op.execute(CreateSchema('categories'))
    op.execute('ALTER TABLE indico.category_index SET SCHEMA categories')
    op.create_table('legacy_id_map',
                    sa.Column('legacy_category_id', sa.String(), nullable=False, index=True),
                    sa.Column('category_id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('legacy_category_id', 'category_id'),
                    schema='categories')


def downgrade():
    op.drop_table('legacy_id_map', schema='categories')
    op.execute('ALTER TABLE categories.category_index SET SCHEMA indico')
    op.execute(DropSchema('categories'))
