"""Reverse Event.category_chain

Revision ID: 18755f50c6e7
Revises: 535f817f2533
Create Date: 2016-06-20 11:55:32.629379
"""

from contextlib import contextmanager

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '18755f50c6e7'
down_revision = '535f817f2533'


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


@contextmanager
def _no_timetable_trigger():
    op.execute('DROP TRIGGER consistent_timetable ON events.events')
    yield
    op.execute('''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');
    ''')


def upgrade():
    op.execute('SET CONSTRAINTS ALL IMMEDIATE')
    op.drop_constraint('ck_events_category_id_matches_chain', 'events', schema='events')
    op.drop_constraint('ck_events_category_chain_has_root', 'events', schema='events')
    with _array_reverse_func(), _no_timetable_trigger():
        op.execute('''
            UPDATE events.events
            SET category_chain = _array_reverse(category_chain)
            WHERE category_chain IS NOT NULL;
        ''')
    op.create_check_constraint('category_id_matches_chain', 'events',
                               'category_id = category_chain[array_length(category_chain, 1)]',
                               schema='events')
    op.create_check_constraint('category_chain_has_root', 'events',
                               'category_chain[1] = 0',
                               schema='events')


def downgrade():
    op.execute('SET CONSTRAINTS ALL IMMEDIATE')
    op.drop_constraint('ck_events_category_id_matches_chain', 'events', schema='events')
    op.drop_constraint('ck_events_category_chain_has_root', 'events', schema='events')
    with _array_reverse_func(), _no_timetable_trigger():
        op.execute('''
            UPDATE events.events
            SET category_chain = _array_reverse(category_chain)
            WHERE category_chain IS NOT NULL;
        ''')
    op.create_check_constraint('category_id_matches_chain', 'events',
                               'category_id = category_chain[1]',
                               schema='events')
    op.create_check_constraint('category_chain_has_root', 'events',
                               'category_chain[array_length(category_chain, 1)] = 0',
                               schema='events')
