"""Use FK for vc created_by_id

Revision ID: 319347ac94fe
Revises: 3f63e79cdada
Create Date: 2015-05-08 16:46:39.501771
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '319347ac94fe'
down_revision = '3f63e79cdada'


def upgrade():
    op.create_foreign_key(None,
                          'vc_rooms', 'users',
                          ['created_by_id'], ['id'],
                          source_schema='events', referent_schema='users')


def downgrade():
    op.drop_constraint('fk_vc_rooms_created_by_id_users', 'vc_rooms', schema='events')
