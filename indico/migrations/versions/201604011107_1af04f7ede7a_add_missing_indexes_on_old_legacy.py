"""Add missing indexes on old legacy mappings

Revision ID: 1af04f7ede7a
Revises: 3d672dc5ee53
Create Date: 2016-03-30 10:00:15.115336
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '1af04f7ede7a'
down_revision = '3d672dc5ee53'


def upgrade():
    op.create_index(None, 'legacy_image_id_map', ['image_id'], schema='events')
    op.create_index(None, 'legacy_page_id_map', ['page_id'], schema='events')


def downgrade():
    op.drop_index(op.f('ix_legacy_page_id_map_page_id'), table_name='legacy_page_id_map', schema='events')
    op.drop_index(op.f('ix_legacy_image_id_map_image_id'), table_name='legacy_image_id_map', schema='events')
