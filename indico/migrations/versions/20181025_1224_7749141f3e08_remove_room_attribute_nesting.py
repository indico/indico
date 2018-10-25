"""Remove room attribute nesting

Revision ID: 7749141f3e08
Revises: ec410be271df
Create Date: 2018-10-25 12:24:52.032136
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '7749141f3e08'
down_revision = 'ec410be271df'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_room_attributes_parent_id_room_attributes', 'room_attributes', schema='roombooking')
    op.drop_column('room_attributes', 'parent_id', schema='roombooking')


def downgrade():
    op.add_column('room_attributes', sa.Column('parent_id', sa.Integer(), nullable=True), schema='roombooking')
    op.create_foreign_key(None, 'room_attributes', 'room_attributes', ['parent_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')
