"""Use JSONB for VCRoom data fields

Revision ID: 57732e1f7e20
Revises: 3bbcba10f5b1
Create Date: 2016-11-29 18:11:36.151951
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '57732e1f7e20'
down_revision = '3bbcba10f5b1'


def upgrade():
    op.execute('ALTER TABLE events.vc_rooms ALTER COLUMN data TYPE jsonb USING data::jsonb')
    op.execute('ALTER TABLE events.vc_room_events ALTER COLUMN data TYPE jsonb USING data::jsonb')


def downgrade():
    op.execute('ALTER TABLE events.vc_rooms ALTER COLUMN data TYPE json USING data::json')
    op.execute('ALTER TABLE events.vc_room_events ALTER COLUMN data TYPE json USING data::json')
