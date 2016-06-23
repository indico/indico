"""Remove Event.category_chain

Revision ID: 81e04fbff5
Revises: 3f25f66e8d5c
Create Date: 2016-06-23 13:37:42.723089
"""

from contextlib import contextmanager

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = '81e04fbff5'
down_revision = '3f25f66e8d5c'


@contextmanager
def _array_reverse_func():
    op.execute('''
        CREATE FUNCTION _array_reverse(anyarray) RETURNS anyarray AS $$
            SELECT ARRAY(
                SELECT $1[i]
                FROM generate_subscripts($1,1) AS s(i)
                ORDER BY i DESC
            );
        $$
        LANGUAGE 'sql' STRICT IMMUTABLE;
    ''')
    yield
    op.execute('DROP FUNCTION _array_reverse(anyarray);')


def upgrade():
    op.drop_constraint('ck_events_category_id_matches_chain', 'events', schema='events')
    op.drop_constraint('ck_events_category_chain_has_root', 'events', schema='events')
    op.drop_constraint('ck_events_category_data_set', 'events', schema='events')
    op.drop_column('events', 'category_chain', schema='events')
    op.create_check_constraint('category_data_set', 'events', 'category_id IS NOT NULL OR is_deleted', schema='events')
    op.create_index('ix_events_not_deleted_category', 'events', ['is_deleted', 'category_id'], schema='events')
    op.create_index('ix_events_not_deleted_category_dates', 'events',
                    ['is_deleted', 'category_id', 'start_dt', 'end_dt'], schema='events')


def downgrade():
    op.drop_index('ix_events_not_deleted_category', 'events', schema='events')
    op.drop_index('ix_events_not_deleted_category_dates', 'events', schema='events')
    op.add_column('events', sa.Column('category_chain', pg.ARRAY(sa.Integer()), nullable=True), schema='events')
    op.create_index(None, 'events', ['category_chain'], unique=False, schema='events', postgresql_using='gin')
    op.create_check_constraint('category_id_matches_chain', 'events',
                               'category_id = category_chain[1]',
                               schema='events')
    op.create_check_constraint('category_chain_has_root', 'events',
                               'category_chain[array_length(category_chain, 1)] = 0',
                               schema='events')
    op.drop_constraint('ck_events_category_data_set', 'events', schema='events')
    _populate_category_chains()
    op.create_check_constraint('category_data_set', 'events',
                               '(category_id IS NOT NULL AND category_chain IS NOT NULL) OR is_deleted',
                               schema='events')


def _populate_category_chains():
    print 'Populating category chains. This may take a long time!'
    op.execute('SET CONSTRAINTS ALL IMMEDIATE;')
    with _array_reverse_func():
        op.execute('''
            WITH RECURSIVE chains(id, path) AS (
                SELECT id, ARRAY[id]
                FROM categories.categories
                WHERE parent_id IS NULL

                UNION ALL

                SELECT cat.id, chains.path || cat.id
                FROM categories.categories cat, chains
                WHERE cat.parent_id = chains.id
            )
            UPDATE events.events e
            SET category_chain = _array_reverse(chains.path)
            FROM chains
            WHERE e.category_id IS NOT NULL AND chains.id = e.category_id;
        ''')
