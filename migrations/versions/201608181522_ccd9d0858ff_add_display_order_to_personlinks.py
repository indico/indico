"""Add display order to PersonLinks

Revision ID: ccd9d0858ff
Revises: 11890f58b1df
Create Date: 2016-08-17 15:22:57.540435
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ccd9d0858ff'
down_revision = '11890f58b1df'


def upgrade():
    op.add_column('contribution_person_links',
                  sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
                  schema='events')
    op.add_column('event_person_links',
                  sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
                  schema='events')
    op.add_column('session_block_person_links',
                  sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
                  schema='events')
    op.add_column('subcontribution_person_links',
                  sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
                  schema='events')
    op.alter_column('contribution_person_links', 'display_order', server_default=None, schema='events')
    op.alter_column('event_person_links', 'display_order', server_default=None, schema='events')
    op.alter_column('session_block_person_links', 'display_order', server_default=None, schema='events')
    op.alter_column('subcontribution_person_links', 'display_order', server_default=None, schema='events')


def downgrade():
    op.drop_column('subcontribution_person_links', 'display_order', schema='events')
    op.drop_column('session_block_person_links', 'display_order', schema='events')
    op.drop_column('event_person_links', 'display_order', schema='events')
    op.drop_column('contribution_person_links', 'display_order', schema='events')
