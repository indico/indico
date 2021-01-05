# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict, defaultdict
from datetime import timedelta
from itertools import takewhile

from flask import render_template, request
from pytz import timezone

from indico.modules.events.layout import layout_settings
from indico.util.date_time import iterdays


def _localized_time(dt, tz):
    return dt.astimezone(tz).time()


def inject_week_timetable(event, days, tz_name, tpl='events/timetable/display/_weeks.html'):
    first_week_day = layout_settings.get(event, 'timetable_theme_settings').get('start_day')
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
        week_table_shallow[-1].append((day, day_dict[day]))

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

    timetable_settings = layout_settings.get(event, 'timetable_theme_settings')
    return render_template(tpl, event=event, week_table=week_table, timetable_settings=timetable_settings,
                           has_weekends=has_weekends, timezone=tz_name, tz_object=tz, show_end_times=show_end_times)
