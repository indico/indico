"""Use new track objects in contributions

Revision ID: 52d970fb6a74
Revises: 55d523872c43
Create Date: 2016-09-16 12:22:38.768263
"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '52d970fb6a74'
down_revision = '55d523872c43'


def upgrade():
    op.drop_column('contributions', 'legacy_track_id', schema='events')
    op.create_foreign_key(None, 'contributions', 'tracks', ['track_id'], ['id'], source_schema='events',
                          referent_schema='events')


def downgrade():
    op.drop_constraint('fk_contributions_track_id_tracks', 'contributions', schema='events')
    op.add_column('contributions', sa.Column('legacy_track_id', sa.Integer(), nullable=True), schema='events')
