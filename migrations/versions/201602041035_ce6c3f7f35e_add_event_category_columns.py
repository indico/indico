"""Add event category columns

Revision ID: ce6c3f7f35e
Revises: 27299745573
Create Date: 2016-02-01 13:58:28.697263
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = 'ce6c3f7f35e'
down_revision = '27299745573'


def upgrade():
    op.add_column('events', sa.Column('category_chain', pg.ARRAY(sa.Integer()), nullable=True), schema='events')
    op.add_column('events', sa.Column('category_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'events', ['category_chain'], unique=False, schema='events', postgresql_using='gin')
    op.create_index(None, 'events', ['category_id'], unique=False, schema='events')
    op.create_check_constraint('category_id_matches_chain', 'events',
                               'category_id = category_chain[1]',
                               schema='events')
    op.create_check_constraint('category_chain_has_root', 'events',
                               'category_chain[array_length(category_chain, 1)] = 0',
                               schema='events')


def downgrade():
    op.drop_constraint('ck_events_category_id_matches_chain', 'events', schema='events')
    op.drop_constraint('ck_events_category_chain_has_root', 'events', schema='events')
    op.drop_column('events', 'category_id', schema='events')
    op.drop_column('events', 'category_chain', schema='events')
