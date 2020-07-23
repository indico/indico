"""Add custom boa file to event

Revision ID: 12fbf6af2367
Revises: d89abffb0f63
Create Date: 2020-07-29 16:02:58.081616
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '12fbf6af2367'
down_revision = 'd89abffb0f63'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('custom_boa_id', sa.Integer(), nullable=True), schema='events')
    op.create_foreign_key(None, 'events', 'files', ['custom_boa_id'], ['id'], source_schema='events', referent_schema='indico')


def downgrade():
    op.drop_column('events', 'custom_boa_id', schema='events')
