"""Sync contribution/abstract friendly ids

Revision ID: 258db7e5a3e5
Revises: 3ca8e62e6c36
Create Date: 2016-04-21 16:56:20.113767
"""

import sqlalchemy as sa
from alembic import context, op


# revision identifiers, used by Alembic.
revision = '258db7e5a3e5'
down_revision = '3ca8e62e6c36'


def _sync_last_contrib_id():
    op.execute("""
        UPDATE events.events e
        SET last_friendly_contribution_id = greatest(
            last_friendly_contribution_id,
            (SELECT MAX(c.friendly_id) FROM events.contributions c WHERE c.event_id = e.id),
            (SELECT MAX(a.friendly_id) FROM event_abstracts.abstracts a WHERE a.event_id = e.id)
        )
        WHERE
            e.id IN (SELECT DISTINCT event_id FROM event_abstracts.abstracts) AND
            last_friendly_contribution_id != greatest(
                last_friendly_contribution_id,
                (SELECT MAX(c.friendly_id) FROM events.contributions c WHERE c.event_id = e.id),
                (SELECT MAX(a.friendly_id) FROM event_abstracts.abstracts a WHERE a.event_id = e.id)
            )
    """)


def _get_next_friendly_id(conn, event_id):
    cur = conn.execute("""
        UPDATE events.events
        SET last_friendly_contribution_id = last_friendly_contribution_id + 1
        WHERE events.events.id = %s
        RETURNING last_friendly_contribution_id
    """, (event_id,))
    return cur.fetchone()[0]


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    # Remove the trigger and unique index since we need to modify events
    # with inconsistencies and also will have friendly_id collisions
    # temporarily
    op.execute("DROP TRIGGER consistent_timetable ON events.events")
    op.drop_index('ix_uq_contributions_friendly_id_event_id', table_name='contributions', schema='events')
    # Sync the friendly ID of contributions with that of their abstract
    op.execute("""
        UPDATE events.contributions c
        SET friendly_id = (
            SELECT friendly_id FROM event_abstracts.abstracts a WHERE a.id = c.abstract_id
        )
        WHERE
            c.abstract_id IS NOT NULL AND
            c.friendly_id != (SELECT friendly_id FROM event_abstracts.abstracts a WHERE a.id = c.abstract_id) AND
            c.event_id IN (SELECT DISTINCT event_id FROM event_abstracts.abstracts)
    """)
    # Synchronize the friendly_id sequences so new contributions/abstracts can be added
    _sync_last_contrib_id()
    # Find contributions which now have friendly_id collisions and assign new ones
    query = """
        SELECT c.id, c.event_id
        FROM events.contributions c
        WHERE
            NOT c.is_deleted AND
            EXISTS (
                SELECT 1
                FROM events.contributions c2
                WHERE
                    c2.event_id = c.event_id AND
                    c2.friendly_id = c.friendly_id AND
                    c2.id != c.id AND
                    c.abstract_id IS NULL
            ) AND
            c.event_id IN (SELECT DISTINCT event_id FROM event_abstracts.abstracts)
    """
    for contrib_id, event_id in conn.execute(query):
        friendly_id = _get_next_friendly_id(conn, event_id)
        print 'Updating friendly contribution ID to avoid collision', event_id, contrib_id, friendly_id
        conn.execute("UPDATE events.contributions SET friendly_id = %s WHERE id = %s", (friendly_id, contrib_id))
    # Assign new friendly IDs to contributions with no abstract that have friendly IDs colliding with abstracts
    query = """
        SELECT c.id, c.event_id
        FROM events.contributions c
        WHERE
            EXISTS (
                SELECT 1
                FROM event_abstracts.abstracts a
                WHERE
                    a.event_id = c.event_id AND
                    a.friendly_id = c.friendly_id AND
                    (c.abstract_id != a.id OR c.abstract_id IS NULL)
            )
    """
    for contrib_id, event_id in conn.execute(query):
        friendly_id = _get_next_friendly_id(conn, event_id)
        print 'Updating friendly contribution ID to avoid future collision', event_id, contrib_id, friendly_id
        conn.execute("UPDATE events.contributions SET friendly_id = %s WHERE id = %s", (friendly_id, contrib_id))
    # The sequences should still be in sync but re-sync them just in case
    _sync_last_contrib_id()
    # Restore the index and triggers
    op.create_index(None, 'contributions', ['friendly_id', 'event_id'], unique=True,
                    postgresql_where=sa.text('NOT is_deleted'), schema='events')
    op.execute("""
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE
        ON events.events
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');
    """)


def downgrade():
    pass
