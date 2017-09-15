"""Add default session to tracks

Revision ID: 1d512a9ebb30
Revises: 790a06790309
Create Date: 2017-09-15 10:23:03.234032
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '1d512a9ebb30'
down_revision = '790a06790309'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tracks', sa.Column('default_session_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'tracks', ['default_session_id'], unique=False, schema='events')
    op.create_foreign_key(None, 'tracks', 'sessions', ['default_session_id'], ['id'], source_schema='events',
                          referent_schema='events')


def downgrade():
    op.drop_column('tracks', 'default_session_id', schema='events')
