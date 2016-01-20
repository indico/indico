"""Add trigger for consistent timetable

Revision ID: 43f6a1414c75
Revises: 29232c09e58a
Create Date: 2016-01-19 17:50:14.391523
"""

import textwrap

from alembic import op


# revision identifiers, used by Alembic.
revision = '43f6a1414c75'
down_revision = '29232c09e58a'


def upgrade():
    op.execute(textwrap.dedent("""
        CREATE OR REPLACE FUNCTION events.check_timetable_consistency() RETURNS trigger AS
        $BODY$
        BEGIN
        IF EXISTS (
            SELECT te.*
            FROM events.timetable_entries te
            WHERE te.parent_id IS NULL AND te.type = 2 AND EXISTS (
                SELECT 1
                FROM events.contributions c
                WHERE c.id = te.contribution_id AND (c.session_id IS NOT NULL or c.session_block_id IS NOT NULL)
            ) AND te.event_id = NEW.event_id
        ) THEN
            RAISE EXCEPTION 'Found top-level timetable entry for contribution in a session';
        END IF;

        IF EXISTS (
            SELECT te.*
            FROM events.timetable_entries te
            JOIN events.timetable_entries tep ON (tep.id = te.parent_id)
            JOIN events.session_blocks sb ON (sb.id = tep.session_block_id)
            WHERE te.parent_id IS NOT NULL AND te.type = 2 AND EXISTS (
                SELECT 1
                FROM events.contributions c
                WHERE (
                    c.id = te.contribution_id AND (COALESCE(c.session_id, -1) != COALESCE(sb.session_id, -1) OR
                    COALESCE(c.session_block_id, -1) != COALESCE(tep.session_block_id, -1))
                )
            ) AND te.event_id = NEW.event_id
        ) THEN
            RAISE EXCEPTION 'Found child timetable entry for contribution in a session that does not match the parent session';
        END IF;
        RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql;
    """))
    op.execute("""
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON events.contributions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency();
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON events.timetable_entries
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency();
    """)


def downgrade():
    op.execute("DROP TRIGGER consistent_timetable ON events.contributions")
    op.execute("DROP TRIGGER consistent_timetable ON events.timetable_entries")
    op.execute("DROP FUNCTION events.check_timetable_consistency()")
