# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import date
from itertools import groupby
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from flask import session

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.modules.events.util import get_base_ical_parameters, serialize_event_for_json_ld
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.flask.util import url_for


def group_by_month(events, now, tzinfo):
    def _format_tuple(x):
        (year, month), events = x
        return {'name': format_date(date(year, month, 1), format='MMMM yyyy'),
                'events': list(events),
                'is_current': year == now.year and month == now.month}

    def _key(event):
        start_dt = event.start_dt.astimezone(tzinfo)
        return start_dt.year, start_dt.month

    months = groupby(events, key=_key)
    return map(_format_tuple, months)


def make_format_event_date_func(category):
    def fn(event):
        day_month = 'dd MMM'
        tzinfo = category.display_tzinfo
        start_dt = event.start_dt.astimezone(tzinfo)
        end_dt = event.end_dt.astimezone(tzinfo)
        if start_dt.year != end_dt.year:
            return '{} - {}'.format(to_unicode(format_date(start_dt, timezone=tzinfo)),
                                    to_unicode(format_date(end_dt, timezone=tzinfo)))
        elif (start_dt.month != end_dt.month) or (start_dt.day != end_dt.day):
            return '{} - {}'.format(to_unicode(format_date(start_dt, day_month, timezone=tzinfo)),
                                    to_unicode(format_date(end_dt, day_month, timezone=tzinfo)))
        else:
            return to_unicode(format_date(start_dt, day_month, timezone=tzinfo))

    return fn


def make_happening_now_func(now):
    return lambda event: event.start_dt <= now < event.end_dt


def make_is_recent_func(now):
    return lambda dt: dt > now - relativedelta(weeks=1)


def get_category_view_params(category, now):
    from .display import RHDisplayCategoryEventsBase

    # Current events, which are always shown by default are events of this month and of the previous month.
    # If there are no events in this range, it will include the last and next month containing events.
    past_threshold = now - relativedelta(months=1, day=1, hour=0, minute=0)
    future_threshold = now + relativedelta(months=1, day=1, hour=0, minute=0)
    hidden_event_ids = {e.id for e in category.get_hidden_events(user=session.user)}
    next_event_start_dt = (db.session.query(Event.start_dt)
                           .filter(Event.start_dt >= now, Event.category_id == category.id,
                                   Event.id.notin_(hidden_event_ids))
                           .order_by(Event.start_dt.asc(), Event.id.asc())
                           .first() or (None,))[0]
    previous_event_start_dt = (db.session.query(Event.start_dt)
                               .filter(Event.start_dt < now, Event.category_id == category.id,
                                       Event.id.notin_(hidden_event_ids))
                               .order_by(Event.start_dt.desc(), Event.id.desc())
                               .first() or (None,))[0]
    if next_event_start_dt is not None and next_event_start_dt > future_threshold:
        future_threshold = next_event_start_dt + relativedelta(months=1, day=1, hour=0, minute=0)
    if previous_event_start_dt is not None and previous_event_start_dt < past_threshold:
        past_threshold = previous_event_start_dt.replace(day=1, hour=0, minute=0)
    event_query = (Event.query.with_parent(category)
                   .options(*RHDisplayCategoryEventsBase._event_query_options)
                   .filter(Event.id.notin_(hidden_event_ids))
                   .order_by(Event.start_dt.desc(), Event.id.desc()))
    past_event_query = event_query.filter(Event.start_dt < past_threshold)
    future_event_query = event_query.filter(Event.start_dt >= future_threshold)
    current_event_query = event_query.filter(Event.start_dt >= past_threshold,
                                             Event.start_dt < future_threshold)
    json_ld_events = events = current_event_query.filter(Event.start_dt < future_threshold).all()

    future_event_count = future_event_query.count()
    past_event_count = past_event_query.count()
    has_hidden_events = bool(hidden_event_ids)

    if not session.user and future_event_count:
        json_ld_events = json_ld_events + future_event_query.all()

    show_future_events = bool(category.id in session.get('fetch_future_events_in', set()) or
                              (session.user and session.user.settings.get('show_future_events', False)))
    show_past_events = bool(category.id in session.get('fetch_past_events_in', set()) or
                            (session.user and session.user.settings.get('show_past_events', False)))

    managers = sorted(category.get_manager_list(), key=attrgetter('principal_type.name', 'name'))

    threshold_format = '%Y-%m'
    params = {'event_count': len(events),
              'events_by_month': group_by_month(events, now, category.tzinfo),
              'format_event_date': make_format_event_date_func(category),
              'future_event_count': future_event_count,
              'show_future_events': show_future_events,
              'future_threshold': future_threshold.strftime(threshold_format),
              'happening_now': make_happening_now_func(now),
              'is_recent': make_is_recent_func(now),
              'managers': managers,
              'past_event_count': past_event_count,
              'show_past_events': show_past_events,
              'past_threshold': past_threshold.strftime(threshold_format),
              'has_hidden_events': has_hidden_events,
              'json_ld': map(serialize_event_for_json_ld, json_ld_events),
              'atom_feed_url': url_for('.export_atom', category),
              'atom_feed_title': _('Events of "{}"').format(category.title)}
    params.update(get_base_ical_parameters(session.user, 'category',
                                           '/export/categ/{0}.ics'.format(category.id), {'from': '-31d'}))
    return params
