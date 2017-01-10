# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import textwrap

from sqlalchemy import DDL

from indico.core import signals


@signals.db_schema_created.connect_via('events')
def _create_check_timetable_consistency(sender, connection, **kwargs):
    sql = textwrap.dedent("""
        CREATE FUNCTION events.check_timetable_consistency() RETURNS trigger AS
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
        LANGUAGE plpgsql
    """)
    DDL(sql).execute(connection)
