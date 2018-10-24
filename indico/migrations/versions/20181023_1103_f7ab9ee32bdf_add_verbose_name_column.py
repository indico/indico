"""Add verbose_name column

Revision ID: f7ab9ee32bdf
Revises: 55893713f6b7
Create Date: 2018-10-23 11:45:07.880418
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f7ab9ee32bdf'
down_revision = '55893713f6b7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rooms', sa.Column('verbose_name', sa.String(), nullable=True), schema='roombooking')
    # set verbose_name only when the name is non-standard (B-F-N)
    op.execute("UPDATE roombooking.rooms SET verbose_name = name "
               "WHERE name != format('%s-%s-%s', building, floor, number)")
    op.create_check_constraint('verbose_name_not_empty', 'rooms', "verbose_name != ''", schema='roombooking')
    op.drop_column('rooms', 'name', schema='roombooking')


def downgrade():
    op.add_column('rooms',
                  sa.Column('name', sa.String(), nullable=True),
                  schema='roombooking')
    op.execute("UPDATE roombooking.rooms SET name = format('%s-%s-%s', building, floor, number) "
               "WHERE verbose_name IS NULL")
    op.execute("UPDATE roombooking.rooms SET name = verbose_name "
               "WHERE verbose_name IS NOT NULL")
    op.alter_column('rooms', 'name', nullable=False, schema='roombooking')
    op.drop_column('rooms', 'verbose_name', schema='roombooking')
