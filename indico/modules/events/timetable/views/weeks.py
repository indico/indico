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

from collections import defaultdict, OrderedDict
from datetime import timedelta
from itertools import takewhile

from flask import render_template, request
from pytz import timezone

from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.util.date_time import iterdays


def _flatten_timetable(entries):
    for entry in entries:
        if entry.type == TimetableEntryType.SESSION_BLOCK:
            for sub_entry in entry.children:
                yield sub_entry
        else:
            yield entry


def _localized_time(dt, tz):
    return dt.astimezone(tz).time()


def inject_week_timetable(event, days, tz_name):
    first_week_day = request.args.get('first_week_day', 'monday')  # monday/sunday/event
    sunday_first = (first_week_day == 'sunday')
    show_end_times = request.args.get('showEndTimes') == '1'

    tz = timezone(tz_name)

    day_dict = defaultdict(list, days)
    sorted_dates = [d.date() for d in iterdays(event.start_dt.astimezone(tz), event.end_dt.astimezone(tz))]
    first_day, last_day = sorted_dates[0], sorted_dates[-1]
    has_weekends = any(d.weekday() in (5, 6) for d in sorted_dates)

    # Calculate the actual starting day, based on the selected first day of the week
    if first_week_day != 'event':
        week_start = 6 if sunday_first else 0
        if first_day.weekday() != week_start:
            first_day -= timedelta(days=first_day.weekday()) + timedelta(days=int(has_weekends and sunday_first))

    week_table_shallow = []
    skipped_days = 0
    for i, dt in enumerate(iterdays(first_day, last_day)):
        day = dt.date()
        if day > last_day:
            # the loop doesn't account for skipped days so we might have to break early
            break
        if not has_weekends and day.weekday() == 5:
            day += timedelta(days=2)
            skipped_days += 2
        if i % (7 if has_weekends else 5) == 0:
            week_table_shallow.append([])
        week_table_shallow[-1].append((day, list(_flatten_timetable(day_dict[day]))))

    # build a new week table that contains placeholders
    week_table = []
    for week in week_table_shallow:
        # Build list of time slots that are used this week
        time_slots = set()
        for day, entries in week:
            time_slots.update(_localized_time(x.start_dt, tz) for x in entries)

        # Build each day with its contributions and placeholders
        tmp = []
        for day, entries in week:
            day_tmp = defaultdict(list)
            for entry in entries:
                day_tmp[_localized_time(entry.start_dt, tz)].append(entry)

            for slot in sorted(time_slots):
                day_tmp.setdefault(slot, [])

            # We've got a dict with a {slot: [entry, entry, ...]} mapping (for a single day)
            # We'll run over it and make some additional calculations
            day_tmp_sorted = sorted(day_tmp.viewitems())
            day_entries = OrderedDict()
            for n, (slot, slot_entries) in enumerate(day_tmp_sorted):
                tmp_slot_entries = []
                for entry in slot_entries:
                    # Check how many empty slots which intersect this one exist
                    count = sum(1 for x in takewhile(lambda x: not x[1], iter(day_tmp_sorted[n + 1:]))
                                if x[0] < _localized_time(entry.end_dt, tz))
                    tmp_slot_entries.append((entry, count))
                day_entries[slot] = tmp_slot_entries
            tmp.append((day, day_entries))
        week_table.append(tmp)

    return render_template('events/timetable/display/_weeks.html', event=event, week_table=week_table,
                           has_weekends=has_weekends, timezone=tz_name, tz_object=tz, show_end_times=show_end_times)
