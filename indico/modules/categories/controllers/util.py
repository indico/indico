# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date
from itertools import groupby
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.categories.models.event_move_request import MoveRequestState
from indico.modules.events.models.events import Event
from indico.modules.events.util import serialize_events_for_json_ld
from indico.util.date_time import format_date, format_skeleton
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.web.flask.util import url_for


def group_by_month(events, now, tzinfo):
    def _format_tuple(x):
        (year, month), events = x
        return {'name': format_skeleton(date(year, month, 1), 'MMMMyyyy'),
                'events': list(events),
                'is_current': year == now.year and month == now.month}

    def _key(event):
        start_dt = event.start_dt.astimezone(tzinfo)
        return start_dt.year, start_dt.month

    months = groupby(events, key=_key)
    return list(map(_format_tuple, months))


def group_by_year(events_by_month, now):
    def _format_year(x):
        year, months = x
        return {
            'year': year,
            'is_current': year == now.year,
            'months': list(months),
        }

    def _key(month):
        __, year = month['name'].rsplit(' ', 1)
        return int(year)

    years = groupby(events_by_month, key=_key)
    return list(map(_format_year, years))


def group_by_year_month(events, now, tzinfo):

    def _format_year(year, months):
        return {
            'year': year,
            'is_current': year == now.year,
            'months': list(months),
        }

    def _format_month(month, events):
        return {
            'name': format_skeleton(date(month[0], month[1], 1), 'MMMMyyyy'),
            'is_current': month[0] == now.year and month[1] == now.month,
            'events': list(events),
        }

    def _year_key(event):
        start_dt = event.start_dt.astimezone(tzinfo)
        return start_dt.year

    def _month_key(event):
        start_dt = event.start_dt.astimezone(tzinfo)
        return start_dt.year, start_dt.month

    result = []

    for year, year_events in groupby(events, key=_year_key):
        months = (_format_month(month, month_events) for month, month_events in groupby(year_events, key=_month_key))

        result.append(_format_year(year, months))
    return result


def serialize_event(event, format_event_date, is_recent, happening_now):
    is_lecture = (event.type == 'lecture')
    if event.series and event.series.show_sequence_in_title:
        series_label = f'({event.series_pos}/{event.series_count})'
    else:
        series_label = None
    return {
        'id': event.id,
        'title': event.title,
        'verbosedTitle': event.get_verbose_title(show_speakers=is_lecture, show_series_pos=False),
        'seriesLabel': series_label,
        'url': event.url,
        'date': format_event_date(event),
        'isRecent': is_recent(event.created_dt),
        'isHappeningNow': happening_now(event),
        'visibility': event.visibility,
        'isProtected': event.is_self_protected,
        'type': event.type,
        'label': event.label.title if event.label else None,
        'labelColor': event.label.color if event.label else None,
        'isFavorite': event in session.user.favorite_events,
    }


def serialize_events_by_year(events_by_year, category, now):
    format_event_date = make_format_event_date_func(category, with_time=True)
    is_recent = make_is_recent_func(now)
    happening_now = make_happening_now_func(now)

    return [
        {
            'year': year['year'],
            'isCurrent': year['is_current'],
            'months': [
                {
                    'name': month['name'],
                    'isCurrent': month['is_current'],
                    'events': [
                        serialize_event(
                            event,
                            format_event_date,
                            is_recent,
                            happening_now,
                        )
                        for event in month['events']
                    ],
                }
                for month in year['months']
            ],
        }
        for year in events_by_year
    ]


def make_format_event_date_func(category, with_time=False):
    day_month = 'ddMMM'
    time = 'HHmm'

    def fn(event):
        tzinfo = category.display_tzinfo
        start_dt = event.start_dt.astimezone(tzinfo)
        end_dt = event.end_dt.astimezone(tzinfo)
        if start_dt.year != end_dt.year:
            return f'{format_date(start_dt, timezone=tzinfo)} - {format_date(end_dt, timezone=tzinfo)}'
        elif (start_dt.month != end_dt.month) or (start_dt.day != end_dt.day):
            start = format_skeleton(start_dt, day_month, timezone=tzinfo)
            end = format_skeleton(end_dt, day_month, timezone=tzinfo)
            return f'{start} - {end}'
        else:
            if with_time:
                return format_skeleton(start_dt, day_month, timezone=tzinfo)+ ' - ' + format_skeleton(start_dt, time,
                                                                                                      timezone=tzinfo)
            return format_skeleton(start_dt, day_month, timezone=tzinfo)

    return fn


def make_happening_now_func(now):
    return lambda event: event.start_dt <= now < event.end_dt


def make_is_recent_func(now):
    return lambda dt: dt > now - relativedelta(weeks=1)


def get_event_query_filter(category, is_flat=False, hidden_event_ids=None):
    criteria = [~Event.is_deleted]
    if is_flat:
        # Hidden events (visibility == 0) are excluded here, but we can't include an OR criterion
        # checking for a direct category id match as this completely destroys the performance of
        # the query.
        # This should be OK though since showing hidden events in the flattened event list isn't
        # important - they would only be shown to category managers and when using the non-flat
        # view they still see them anyway.
        criteria.append(Event.is_visible_in(category.id))
    else:
        criteria.append(Event.category_id == category.id)
    if hidden_event_ids:
        criteria.append(Event.id.notin_(hidden_event_ids))
    return db.and_(*criteria)


def get_category_view_params(category, now, is_flat=False):
    from .display import RHDisplayCategoryEventsBase

    # Current events, which are always shown by default are events of this month and of the previous month.
    # If there are no events in this range, it will include the last and next month containing events.

    past_threshold = now - relativedelta(months=1, day=1, hour=0, minute=0)
    future_threshold = now + relativedelta(months=category.show_future_months+1, day=1, hour=0, minute=0)

    hidden_event_ids = {e.id for e in category.get_hidden_events(user=session.user)} if not is_flat else set()
    event_query_filter = get_event_query_filter(category, is_flat=is_flat, hidden_event_ids=hidden_event_ids)

    extra_events_queries = extra_events_start_dt_queries = ()
    extra_event_ids = values_from_signal(signals.category.extra_events.send(category, is_flat=is_flat,
                                                                            past_threshold=past_threshold,
                                                                            future_threshold=future_threshold))
    if extra_event_ids:
        extra_events_start_dt_queries = [db.session.query(Event.id, Event.start_dt)
                                         .filter(Event.id.in_(extra_event_ids))]
        extra_events_queries = [Event.query.filter(Event.id.in_(extra_event_ids))]

    next_event_start_dt = (db.session.query(Event.id, Event.start_dt)
                           .filter(event_query_filter, Event.start_dt >= now)
                           .union(*extra_events_start_dt_queries)
                           .with_entities(Event.start_dt)
                           .order_by(Event.start_dt.asc(), Event.id.asc())
                           .limit(1).scalar())
    previous_event_start_dt = (db.session.query(Event.id, Event.start_dt)
                               .filter(event_query_filter, Event.start_dt < now)
                               .union(*extra_events_start_dt_queries)
                               .with_entities(Event.start_dt)
                               .order_by(Event.start_dt.desc(), Event.id.desc())
                               .limit(1).scalar())
    if next_event_start_dt is not None and next_event_start_dt > future_threshold:
        future_threshold = next_event_start_dt + relativedelta(months=1, day=1, hour=0, minute=0)
    if previous_event_start_dt is not None and previous_event_start_dt < past_threshold:
        past_threshold = previous_event_start_dt.replace(day=1, hour=0, minute=0)
    event_query = (Event.query
                   .options(*RHDisplayCategoryEventsBase._event_query_options)
                   .filter(event_query_filter)
                   .union(*extra_events_queries)
                   .order_by(Event.start_dt.desc(), Event.id.desc()))
    past_event_query = event_query.filter(Event.start_dt < past_threshold)
    future_event_query = event_query.filter(Event.start_dt >= future_threshold)
    current_event_query = event_query.filter(Event.start_dt >= past_threshold,
                                             Event.start_dt < future_threshold)
    events = current_event_query.all()

    future_event_count = future_event_query.count()
    past_event_count = past_event_query.count()
    has_hidden_events = bool(hidden_event_ids)

    json_ld_events = events[:]
    if not session.user and future_event_count:
        json_ld_events += future_event_query.all()

    show_future_events = bool(category.id in session.get('fetch_future_events_in', set()) or
                              (session.user and session.user.settings.get('show_future_events', False)))
    show_past_events = bool(category.id in session.get('fetch_past_events_in', set()) or
                            (session.user and session.user.settings.get('show_past_events', False)))

    managers = sorted(category.get_manager_list(), key=attrgetter('principal_type.name', 'name'))
    pending_event_moves = 0
    if category.can_manage(session.user):
        pending_event_moves = category.event_move_requests.filter_by(state=MoveRequestState.pending).count()

    threshold_format = '%Y-%m'
    return {
        'event_count': len(events),
        'events_by_month': group_by_month(events, now, category.tzinfo),
        'format_event_date': make_format_event_date_func(category),
        'future_event_count': future_event_count,
        'show_future_events': show_future_events,
        'future_threshold': future_threshold.strftime(threshold_format),
        'happening_now': make_happening_now_func(now),
        'is_recent': make_is_recent_func(now),
        'is_flat': is_flat,
        'managers': managers,
        'past_event_count': past_event_count,
        'show_past_events': show_past_events,
        'past_threshold': past_threshold.strftime(threshold_format),
        'has_hidden_events': has_hidden_events,
        'json_ld': serialize_events_for_json_ld(json_ld_events),
        'atom_feed_url': url_for('.export_atom', category),
        'atom_feed_title': _('Events of "{}"').format(category.title),
        'pending_event_moves': pending_event_moves,
    }
