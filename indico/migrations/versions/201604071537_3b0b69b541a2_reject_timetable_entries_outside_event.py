"""Reject timetable entries outside event bounds

Revision ID: 3b0b69b541a2
Revises: 1af04f7ede7a
Create Date: 2016-04-07 15:37:31.908876
"""

import textwrap

from alembic import op


# revision identifiers, used by Alembic.
revision = '3b0b69b541a2'
down_revision = '1af04f7ede7a'


def upgrade():
    op.execute(textwrap.dedent("""
        CREATE OR REPLACE FUNCTION events.check_timetable_consistency() RETURNS trigger AS
        $BODY$
        DECLARE
            src varchar;
            trigger_event_id int;
        BEGIN
        src := TG_ARGV[0];

        IF src = 'break' THEN
            SELECT tte.event_id INTO STRICT trigger_event_id
            FROM events.timetable_entries tte
            WHERE tte.break_id = NEW.id;
        ELSIF src = 'session_block' THEN
            SELECT s.event_id INTO STRICT trigger_event_id
            FROM events.sessions s
            WHERE s.id = NEW.session_id;
        ELSIF src = 'event' THEN
            trigger_event_id := NEW.id;
        ELSE
            trigger_event_id := NEW.event_id;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            WHERE te.parent_id IS NULL AND te.type = 2 AND EXISTS (
                SELECT 1
                FROM events.contributions c
                WHERE c.id = te.contribution_id AND (c.session_id IS NOT NULL or c.session_block_id IS NOT NULL)
            ) AND te.event_id = trigger_event_id
        ) THEN
            RAISE EXCEPTION SQLSTATE 'INDX0' USING
                MESSAGE = 'Timetable inconsistent',
                DETAIL = 'Top-level entry for contribution in a session';
        END IF;

        IF EXISTS (
            SELECT 1
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
            ) AND te.event_id = trigger_event_id
        ) THEN
            RAISE EXCEPTION SQLSTATE 'INDX0' USING
                MESSAGE = 'Timetable inconsistent',
                DETAIL = 'Child entry for contribution in a session does not match the parent session';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            JOIN events.timetable_entries tep ON (tep.id = te.parent_id)
            WHERE te.event_id = trigger_event_id AND te.parent_id IS NOT NULL AND tep.start_dt > te.start_dt
        ) THEN
            RAISE EXCEPTION SQLSTATE 'INDX0' USING
                MESSAGE = 'Timetable inconsistent',
                DETAIL = 'Entry starts before its parent block';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            JOIN events.timetable_entries tep ON (tep.id = te.parent_id)
            JOIN events.session_blocks bl ON (bl.id = tep.session_block_id)
            LEFT JOIN events.contributions c ON (c.id = te.contribution_id)
            LEFT JOIN events.breaks b ON (b.id = te.break_id)
            WHERE te.event_id = trigger_event_id AND te.parent_id IS NOT NULL AND te.type IN (2, 3) AND
                  (te.start_dt + COALESCE(c.duration, b.duration)) > (tep.start_dt + bl.duration)
        ) THEN
            RAISE EXCEPTION SQLSTATE 'INDX0' USING
                MESSAGE = 'Timetable inconsistent',
                DETAIL = 'Entry ends after its parent block';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            JOIN events.events e ON (e.id = te.event_id)
            WHERE te.event_id = trigger_event_id AND te.start_dt < e.start_dt
        ) THEN
            RAISE EXCEPTION SQLSTATE 'INDX0' USING
                MESSAGE = 'Timetable inconsistent',
                DETAIL = 'Entry starts before the event';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            JOIN events.events e ON (e.id = te.event_id)
            LEFT JOIN events.session_blocks bl ON (bl.id = te.session_block_id)
            LEFT JOIN events.contributions c ON (c.id = te.contribution_id)
            LEFT JOIN events.breaks b ON (b.id = te.break_id)
            WHERE te.event_id = trigger_event_id AND
                  (te.start_dt + COALESCE(c.duration, b.duration, bl.duration)) > e.end_dt
        ) THEN
            RAISE EXCEPTION SQLSTATE 'INDX0' USING
                MESSAGE = 'Timetable inconsistent',
                DETAIL = 'Entry ends after the event';
        END IF;

        RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql;
    """))


def downgrade():
    op.execute(textwrap.dedent("""
        CREATE OR REPLACE FUNCTION events.check_timetable_consistency() RETURNS trigger AS
        $BODY$
        DECLARE
            src varchar;
            trigger_event_id int;
        BEGIN
        src := TG_ARGV[0];

        IF src = 'break' THEN
            SELECT tte.event_id INTO STRICT trigger_event_id
            FROM events.timetable_entries tte
            WHERE tte.break_id = NEW.id;
        ELSIF src = 'session_block' THEN
            SELECT s.event_id INTO STRICT trigger_event_id
            FROM events.sessions s
            WHERE s.id = NEW.session_id;
        ELSIF src = 'event' THEN
            trigger_event_id := NEW.id;
        ELSE
            trigger_event_id := NEW.event_id;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            WHERE te.parent_id IS NULL AND te.type = 2 AND EXISTS (
                SELECT 1
                FROM events.contributions c
                WHERE c.id = te.contribution_id AND (c.session_id IS NOT NULL or c.session_block_id IS NOT NULL)
            ) AND te.event_id = trigger_event_id
        ) THEN
            RAISE EXCEPTION 'Found top-level timetable entry for contribution in a session';
        END IF;

        IF EXISTS (
            SELECT 1
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
            ) AND te.event_id = trigger_event_id
        ) THEN
            RAISE EXCEPTION 'Found child timetable entry for contribution in a session that does not match the parent session';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            JOIN events.timetable_entries tep ON (tep.id = te.parent_id)
            WHERE te.event_id = trigger_event_id AND te.parent_id IS NOT NULL AND tep.start_dt > te.start_dt
        ) THEN
            RAISE EXCEPTION 'Found timetable entry starting before its parent block';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM events.timetable_entries te
            JOIN events.timetable_entries tep ON (tep.id = te.parent_id)
            JOIN events.session_blocks bl ON (bl.id = tep.session_block_id)
            LEFT JOIN events.contributions c ON (c.id = te.contribution_id)
            LEFT JOIN events.breaks b ON (b.id = te.break_id)
            WHERE te.event_id = trigger_event_id AND te.parent_id IS NOT NULL AND te.type IN (2, 3) AND
                  (te.start_dt + COALESCE(c.duration, b.duration)) > (tep.start_dt + bl.duration)
        ) THEN
            RAISE EXCEPTION 'Found timetable entry ending after its parent block';
        END IF;

        RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql;
    """))
