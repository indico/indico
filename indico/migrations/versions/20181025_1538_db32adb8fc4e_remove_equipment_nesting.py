"""Remove equipment nesting

Revision ID: db32adb8fc4e
Revises: 7749141f3e08
Create Date: 2018-10-25 15:38:52.413277
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'db32adb8fc4e'
down_revision = '7749141f3e08'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_equipment_types_parent_id_equipment_types', 'equipment_types', schema='roombooking')
    op.drop_column('equipment_types', 'parent_id', schema='roombooking')


def downgrade():
    op.add_column('equipment_types', sa.Column('parent_id', sa.Integer(), nullable=True), schema='roombooking')
    op.create_foreign_key(None, 'equipment_types', 'equipment_types', ['parent_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')
