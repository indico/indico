# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time, timedelta
from enum import Enum, auto
from functools import partial
from io import BytesIO
from itertools import chain, groupby
from operator import attrgetter, itemgetter
from time import mktime

import dateutil
from dateutil.parser import ParserError
from dateutil.relativedelta import relativedelta
from flask import flash, jsonify, redirect, request, session
from marshmallow_enum import EnumField
from pytz import utc
from sqlalchemy.orm import joinedload, load_only, selectinload, subqueryload, undefer, undefer_group
from webargs import fields, validate
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import get_n_matching
from indico.modules.categories.controllers.base import RHCategoryBase, RHDisplayCategoryBase
from indico.modules.categories.controllers.util import (get_category_view_params, get_event_query_filter,
                                                        group_by_month, make_format_event_date_func,
                                                        make_happening_now_func, make_is_recent_func)
from indico.modules.categories.models.categories import Category
from indico.modules.categories.serialize import (serialize_categories_ical, serialize_category, serialize_category_atom,
                                                 serialize_category_chain)
from indico.modules.categories.util import get_category_stats, get_upcoming_events
from indico.modules.categories.views import WPCategory, WPCategoryCalendar
from indico.modules.events.management.settings import global_event_settings
from indico.modules.events.models.events import Event
from indico.modules.events.timetable.util import get_category_timetable
from indico.modules.news.util import get_recent_news
from indico.modules.rb.models.locations import Location
from indico.modules.users import User
from indico.modules.users.models.favorites import favorite_category_table, favorite_event_table
from indico.util.colors import generate_contrast_colors
from indico.util.date_time import format_date, format_number, now_utc
from indico.util.decorators import classproperty
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.marshmallow import LowercaseString, not_empty
from indico.util.signals import values_from_signal
from indico.util.string import crc32
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.rh import RH, allow_signed_url
from indico.web.util import jsonify_data


def _flat_map(func, list_):
    return chain.from_iterable(map(func, list_))


class RHCategoryIcon(RHDisplayCategoryBase):
    _category_query_options = (undefer('icon'),)

    def _check_access(self):
        # Category icons are always public
        pass

    def _process(self):
        if not self.category.has_icon:
            raise NotFound
        metadata = self.category.icon_metadata
        return send_file(metadata['filename'], BytesIO(self.category.icon), mimetype=metadata['content_type'],
                         conditional=True)


class RHCategoryLogo(RHDisplayCategoryBase):
    _category_query_options = (undefer('logo'),)

    def _process(self):
        if not self.category.has_logo:
            raise NotFound
        metadata = self.category.logo_metadata
        return send_file(metadata['filename'], BytesIO(self.category.logo), mimetype=metadata['content_type'],
                         conditional=True)


class RHCategoryStatisticsJSON(RHDisplayCategoryBase):
    def _process(self):
        stats = get_category_stats(self.category.id)
        if 'min_year' not in stats:
            # in case the instance was freshly updated and still has data
            # cached we need to invalidate it to avoid breaking the page
            # TODO: remove this in 3.0; by then people had enough time to update to 2.3...
            get_category_stats.clear_cached(self.category.id)
            stats = get_category_stats(self.category.id)
        data = {
            'events': stats['events_by_year'],
            'contributions': stats['contribs_by_year'],
            'files': stats['attachments'],
            'updated': stats['updated'].isoformat(),
            'total_events': sum(stats['events_by_year'].values()),
            'total_contributions': sum(stats['contribs_by_year'].values()),
            'min_year': stats['min_year'],
            'max_year': date.today().year,
        }
        if self.category.is_root:
            data['users'] = User.query.filter_by(is_deleted=False, is_pending=False).count()
        return jsonify(data)


class RHCategoryStatistics(RHDisplayCategoryBase):
    def _process(self):
        if request.accept_mimetypes.best_match(('application/json', 'text/html')) == 'application/json':
            return redirect(url_for('categories.statistics_json', category_id=self.category.id))
        return WPCategory.render_template('category_statistics.html', self.category)


class RHCategoryInfo(RHDisplayCategoryBase):
    @classproperty
    @classmethod
    def _category_query_options(cls):
        children_strategy = subqueryload('children')
        children_strategy.load_only('id', 'parent_id', 'title', 'protection_mode', 'event_creation_mode')
        children_strategy.subqueryload('acl_entries')
        children_strategy.undefer('deep_children_count')
        children_strategy.undefer('deep_events_count')
        children_strategy.undefer('has_events')
        children_strategy.undefer('has_children')
        return (children_strategy,
                load_only('id', 'parent_id', 'title', 'protection_mode'),
                subqueryload('acl_entries'),
                undefer('deep_children_count'),
                undefer('deep_events_count'),
                undefer('has_events'),
                undefer('has_children'),
                undefer('chain'))

    def _process(self):
        return jsonify_data(flash=False,
                            **serialize_category_chain(self.category, include_children=True, include_parents=True))


class RHReachableCategoriesInfo(RH):
    def _get_reachable_categories(self, id_, excluded_ids):
        cat = Category.query.filter_by(id=id_).options(joinedload('children').load_only('id')).first_or_404()
        ids = ({c.id for c in cat.children} | {c.id for c in cat.parent_chain_query}) - excluded_ids
        if not ids:
            return []
        return (Category.query
                .filter(Category.id.in_(ids))
                .options(*RHCategoryInfo._category_query_options)
                .all())

    @use_kwargs({
        'excluded_ids': fields.List(fields.Int(), data_key='exclude', load_default=None)
    })
    def _process(self, excluded_ids):
        excluded_ids = set(excluded_ids) if excluded_ids is not None else set()
        categories = self._get_reachable_categories(request.view_args['category_id'], excluded_ids=excluded_ids)
        return jsonify_data(categories=[serialize_category_chain(c, include_children=True) for c in categories],
                            flash=False)


class RHCategorySearch(RH):
    def _process(self):
        q = request.args['q'].lower()
        query = (Category.query
                 .filter(Category.title_matches(q),
                         ~Category.is_deleted)
                 .options(undefer('deep_children_count'), undefer('deep_events_count'), undefer('has_events'),
                          undefer('has_children'), joinedload('acl_entries')))
        if session.user:
            # Prefer favorite categories
            query = query.order_by(Category.favorite_of.any(favorite_category_table.c.user_id == session.user.id)
                                   .desc())
        # Prefer exact matches and matches at the beginning, then order by category title and if
        # those are identical by the chain titles
        query = (query
                 .order_by((db.func.lower(Category.title) == q).desc(),
                           db.func.lower(Category.title).startswith(q).desc(),
                           db.func.lower(Category.title),
                           Category.chain_titles))
        total_count = query.count()
        query = query.limit(10)
        return jsonify_data(categories=[serialize_category(c, with_favorite=True, with_path=True) for c in query],
                            total_count=total_count, flash=False)


class RHCategoryManagedEventSearch(RHCategoryBase):
    """Search managed events in a category."""

    def _check_access(self):
        if not session.user:
            raise Forbidden
        RHCategoryBase._check_access(self)

    @use_kwargs({'q': LowercaseString(required=True, validate=not_empty),
                 'offset': fields.Integer(load_default=0, validate=validate.Range(0))}, location='query')
    def _process(self, q, offset):
        from indico.modules.events.series.schemas import SeriesManagementSearchResultsSchema
        query = (
            Event.query.with_parent(self.category)
            .filter(Event.title_matches(q), ~Event.is_deleted)
            .options(load_only('id', 'title', 'start_dt', 'end_dt', 'category_id', 'category_chain', 'series_id'))
        )
        # Prefer favorite events
        query = query.order_by(Event.favorite_of.any(favorite_event_table.c.user_id == session.user.id).desc())
        # Prefer exact matches and matches at the beginning, then order by event title
        query = query.order_by(
            (db.func.lower(Event.title) == q).desc(),
            db.func.lower(Event.title).startswith(q).desc(),
            Event.start_dt,
            db.func.lower(Event.title),
        )
        events_per_page = 10
        # Try to load one extra event. This tells us if there are more events to load later
        events = get_n_matching(query, events_per_page + 1, lambda event: event.can_manage(session.user), offset=offset)
        return SeriesManagementSearchResultsSchema().jsonify({'events': events[:events_per_page],
                                                              'has_more': len(events) > events_per_page})


class RHSubcatInfo(RHDisplayCategoryBase):
    """Get basic information about subcategories.

    This is intended to return information shown on a category display
    page that is not needed immediately and is somewhat expensive to
    retrieve.
    """

    @classproperty
    @classmethod
    def _category_query_options(cls):
        children_strategy = joinedload('children')
        children_strategy.load_only('id')
        children_strategy.undefer('deep_events_count')
        return children_strategy, load_only('id', 'parent_id', 'protection_mode')

    def _process(self):
        event_counts = {c.id: {'value': c.deep_events_count, 'pretty': format_number(c.deep_events_count)}
                        for c in self.category.children}
        return jsonify_data(flash=False, event_counts=event_counts)


class RHDisplayCategoryEventsBase(RHDisplayCategoryBase):
    """Base class for display pages displaying an event list."""

    _category_query_options = (joinedload('children').load_only('id', 'title', 'protection_mode'),
                               undefer('attachment_count'), undefer('has_events'))
    _event_query_options = (joinedload('person_links'), joinedload('series'), undefer_group('series'),
                            joinedload('label'),
                            load_only('id', 'category_id', 'created_dt', 'start_dt', 'end_dt', 'timezone',
                                      'protection_mode', 'title', 'type_', 'series_pos', 'series_count',
                                      'own_address', 'own_venue_id', 'own_venue_name', 'label_id', 'label_message',
                                      'visibility'))

    def _process_args(self):
        RHDisplayCategoryBase._process_args(self)
        self.now = now_utc(exact=False).astimezone(self.category.display_tzinfo)
        self.is_flat = request.args.get('flat') == '1' and self.category.is_flat_view_enabled


class RHDisplayCategory(RHDisplayCategoryEventsBase):
    """Show the contents of a category (events/subcategories)."""

    def _process(self):
        params = get_category_view_params(self.category, self.now, is_flat=self.is_flat)
        if not self.category.is_root:
            return WPCategory.render_template('display/category.html', self.category, **params)

        news = get_recent_news()
        upcoming_events = get_upcoming_events()
        return WPCategory.render_template('display/root_category.html', self.category, news=news,
                                          upcoming_events=upcoming_events, **params)


class RHEventList(RHDisplayCategoryEventsBase):
    """Return the HTML for the event list before/after a specific month."""

    def _parse_year_month(self, string):
        try:
            dt = datetime.strptime(string, '%Y-%m')
        except (TypeError, ValueError):
            return None
        return self.category.display_tzinfo.localize(dt)

    def _process_args(self):
        RHDisplayCategoryEventsBase._process_args(self)
        before = self._parse_year_month(request.args.get('before'))
        after = self._parse_year_month(request.args.get('after'))
        if before is None and after is None:
            raise BadRequest('"before" or "after" parameter must be specified')
        hidden_event_ids = ({e.id for e in self.category.get_hidden_events(user=session.user)}
                            if not self.is_flat else set())
        event_query_filter = get_event_query_filter(self.category, is_flat=self.is_flat,
                                                    hidden_event_ids=hidden_event_ids)

        extra_event_ids = values_from_signal(signals.category.extra_events.send(self.category, is_flat=self.is_flat,
                                                                                before=before, after=after))
        extra_events_queries = [Event.query.filter(Event.id.in_(extra_event_ids))] if extra_event_ids else []

        event_query = (Event.query
                       .options(*self._event_query_options)
                       .filter(event_query_filter)
                       .union(*extra_events_queries)
                       .order_by(Event.start_dt.desc(), Event.id.desc()))
        if before:
            event_query = event_query.filter(Event.start_dt < before)
        if after:
            event_query = event_query.filter(Event.start_dt >= after)
        self.events = event_query.all()

    def _process(self):
        tpl = get_template_module('categories/display/event_list.html')
        html = tpl.event_list_block(events_by_month=group_by_month(self.events, self.now, self.category.tzinfo),
                                    format_event_date=make_format_event_date_func(self.category),
                                    is_recent=make_is_recent_func(self.now),
                                    happening_now=make_happening_now_func(self.now))
        return jsonify_data(flash=False, html=html)


class RHShowEventsInCategoryBase(RHDisplayCategoryBase):
    """Set whether the events in a category are automatically displayed or not."""

    session_field = ''

    def _show_events(self, show_events):
        category_ids = session.setdefault(self.session_field, set())
        if show_events:
            category_ids.add(self.category.id)
        else:
            category_ids.discard(self.category.id)
        session.modified = True

    def _process_DELETE(self):
        self._show_events(False)

    def _process_PUT(self):
        self._show_events(True)


class RHShowFutureEventsInCategory(RHShowEventsInCategoryBase):
    """Set whether the past events in a category are automatically displayed or not."""

    session_field = 'fetch_future_events_in'


class RHShowPastEventsInCategory(RHShowEventsInCategoryBase):
    """Set whether the past events in a category are automatically displayed or not."""

    session_field = 'fetch_past_events_in'


@allow_signed_url
class RHExportCategoryICAL(RHDisplayCategoryBase):
    def _process(self):
        filename = f'{secure_filename(self.category.title, str(self.category.id))}-category.ics'
        buf = serialize_categories_ical([self.category.id], session.user,
                                        Event.end_dt >= (now_utc() - timedelta(weeks=4)))
        return send_file(filename, buf, 'text/calendar')


class RHExportCategoryAtom(RHDisplayCategoryBase):
    def _process(self):
        filename = f'{secure_filename(self.category.title, str(self.category.id))}-category.atom'
        buf = serialize_category_atom(self.category,
                                      url_for(request.endpoint, self.category, _external=True),
                                      session.user,
                                      Event.end_dt >= now_utc())
        return send_file(filename, buf, 'application/atom+xml')


class RHCategoryOverview(RHDisplayCategoryBase):
    """Display the events for a particular day, week or month."""

    def _get_timetable(self):
        return get_category_timetable([self.category.id], self.start_dt, self.end_dt,
                                      detail_level=self.detail, tz=self.category.display_tzinfo,
                                      from_categ=self.category, grouped=False)

    def _process_args(self):
        RHDisplayCategoryBase._process_args(self)
        self.detail = request.args.get('detail', 'event')
        if self.detail not in ('event', 'session', 'contribution'):
            raise BadRequest('Invalid detail argument')
        self.period = request.args.get('period', 'day')
        if self.period not in ('day', 'month', 'week'):
            raise BadRequest('Invalid period argument')
        if 'date' in request.args:
            try:
                date = datetime.strptime(request.args['date'], '%Y-%m-%d')
            except ValueError:
                raise BadRequest('Invalid date argument')
        else:
            date = datetime.now()
        date = self.category.display_tzinfo.localize(date)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        if self.period == 'day':
            self.start_dt = date
            self.end_dt = self.start_dt + relativedelta(days=1)
        elif self.period == 'week':
            self.start_dt = date - relativedelta(days=date.weekday())
            self.end_dt = self.start_dt + relativedelta(days=7)
        elif self.period == 'month':
            self.start_dt = date + relativedelta(day=1)
            self.end_dt = self.start_dt + relativedelta(months=1)

    def _process(self):
        info = self._get_timetable()
        events = info['events']

        # Only categories with icons are listed in the sidebar
        subcategory_ids = {event.category.effective_icon_data['source_id']
                           for event in events if event.category.has_effective_icon}
        subcategories = Category.query.filter(Category.id.in_(subcategory_ids)).all()

        # Events spanning multiple days must appear on all days
        events = _flat_map(partial(self._process_multiday_events, info), events)

        def _event_sort_key(event):
            # Ongoing events are shown after all other events on the same day and are sorted by start_date
            ongoing = getattr(event, 'ongoing', False)
            return (event.start_dt.date(), ongoing,
                    -mktime(event.first_occurence_start_dt.timetuple()) if ongoing else event.start_dt.time())
        events = sorted(events, key=_event_sort_key)

        params = {
            'detail': self.detail,
            'period': self.period,
            'subcategories': subcategories,
            'start_dt': self.start_dt,
            'end_dt': self.end_dt - relativedelta(days=1),  # Display a close-ended interval
            'previous_day_url': self._other_day_url(self.start_dt - relativedelta(days=1)),
            'next_day_url': self._other_day_url(self.start_dt + relativedelta(days=1)),
            'previous_month_url': self._other_day_url(self.start_dt - relativedelta(months=1)),
            'next_month_url': self._other_day_url(self.start_dt + relativedelta(months=1)),
            'previous_year_url': self._other_day_url(self.start_dt - relativedelta(years=1)),
            'next_year_url': self._other_day_url(self.start_dt + relativedelta(years=1)),
            'mathjax': True
        }

        if self.detail != 'event':
            cte = self.category.get_protection_parent_cte()
            params['accessible_categories'] = {cat_id
                                               for cat_id, prot_parent_id in db.session.query(cte)
                                               if prot_parent_id == self.category.id}

        if self.period == 'day':
            return WPCategory.render_template('display/overview/day.html', self.category, events=events, **params)
        elif self.period == 'week':
            days = self._get_week_days()
            template = 'display/overview/week.html'
            params['previous_week_url'] = self._other_day_url(self.start_dt - relativedelta(days=7))
            params['next_week_url'] = self._other_day_url(self.start_dt + relativedelta(days=7))
        elif self.period == 'month':
            days = self._get_calendar_days()
            template = 'display/overview/month.html'

        events_by_day = [
            (day, self._pop_head_while(lambda x: x.start_dt.date() <= day.date(), events))  # noqa: B023
            for day in days
        ]

        # Check whether all weekends are empty
        hide_weekend = (not any(map(itemgetter(1), events_by_day[5::7])) and
                        not any(map(itemgetter(1), events_by_day[6::7])))
        if hide_weekend:
            events_by_day = [x for x in events_by_day if x[0].weekday() not in (5, 6)]

        return WPCategory.render_template(template, self.category, events_by_day=events_by_day,
                                          hide_weekend=hide_weekend, **params)

    def _get_week_days(self):
        # Return the days shown in the weekly overview
        return self._get_days(self.start_dt, self.end_dt)

    def _get_calendar_days(self):
        # Return the days shown in the monthly overview
        start_dt = self.start_dt - relativedelta(days=self.start_dt.weekday())
        end_dt = self.end_dt + relativedelta(days=(7 - self.end_dt.weekday()) % 7)
        return self._get_days(start_dt, end_dt)

    @staticmethod
    def _get_days(start_dt, end_dt):
        # Return all days in the open-ended interval
        current_dt = start_dt
        tz = current_dt.tzinfo
        next_day = current_dt.date() + timedelta(1)
        beginning_of_next_day = tz.localize(datetime.combine(next_day, time()))
        while current_dt < end_dt:
            yield current_dt
            current_dt = beginning_of_next_day
            beginning_of_next_day = current_dt + relativedelta(days=1)

    @staticmethod
    def _pop_head_while(predicate, list_):
        # Pop the head of the list while the predicate is true and return the popped elements
        res = []
        while len(list_) and predicate(list_[0]):
            res.append(list_[0])
            list_.pop(0)
        return res

    def _other_day_url(self, date):
        return url_for('.overview', self.category, detail=self.detail, period=self.period,
                       date=format_date(date, 'yyyy-MM-dd'))

    def _process_multiday_events(self, info, event):
        # Add "fake" proxy events for events spanning multiple days such that there is one event per day
        # Function type: Event -> List[Event]
        tzinfo = self.category.display_tzinfo

        # Breaks, contributions and sessions grouped by start_dt. Each EventProxy will return the relevant ones only
        timetable_objects = sorted(chain(*list(info[event.id].values())), key=attrgetter('timetable_entry.start_dt'))
        timetable_objects_by_date = {x[0]: list(x[1]) for x
                                     in groupby(timetable_objects, key=lambda x: x.start_dt.astimezone(tzinfo).date())}

        # All the days of the event shown in the overview
        event_days = self._get_days(max(self.start_dt, event.start_dt.astimezone(tzinfo)),
                                    min(self.end_dt, event.end_dt.astimezone(tzinfo)))

        # Generate a proxy object with adjusted start_dt and timetable_objects for each day
        return [_EventProxy(event, day, tzinfo, timetable_objects_by_date.get(day.date(), [])) for day in event_days]


class _EventProxy:
    def __init__(self, event, date, tzinfo, timetable_objects):
        start_dt = datetime.combine(date, event.start_dt.astimezone(tzinfo).timetz())
        assert date >= event.start_dt
        assert date <= event.end_dt
        object.__setattr__(self, '_start_dt', start_dt)
        object.__setattr__(self, '_real_event', event)
        object.__setattr__(self, '_event_tz_start_date', event.start_dt.astimezone(tzinfo).date())
        object.__setattr__(self, '_timetable_objects', timetable_objects)

    def __getattribute__(self, name):
        if name == 'start_dt':
            return object.__getattribute__(self, '_start_dt')
        event = object.__getattribute__(self, '_real_event')
        if name == 'timetable_objects':
            return object.__getattribute__(self, '_timetable_objects')
        if name == 'ongoing':
            # the event is "ongoing" if the dates (in the tz of the category)
            # of the event and the proxy (calendar entry) don't match
            event_start_date = object.__getattribute__(self, '_event_tz_start_date')
            return event_start_date != self.start_dt.date()
        if name == 'first_occurence_start_dt':
            return event.start_dt
        return getattr(event, name)

    def __setattr__(self, name, value):
        raise AttributeError('This instance is read-only')

    def __repr__(self):
        return '<_EventProxy({}, {})>'.format(self.start_dt, object.__getattribute__(self, '_real_event'))


class RHCategoryCalendarView(RHDisplayCategoryBase):
    def _process(self):
        return WPCategoryCalendar.render_template('display/calendar.html', self.category)


class RHCategoryCalendarViewEvents(RHDisplayCategoryBase):
    class GroupBy(Enum):
        category = auto()
        location = auto()
        room = auto()
        keywords = auto()

    @use_kwargs({'group_by': EnumField(GroupBy, load_default=GroupBy.category)}, location='query')
    def _process_args(self, group_by):
        RHDisplayCategoryBase._process_args(self)
        tz = self.category.display_tzinfo
        self.group_by = group_by
        try:
            self.start_dt = tz.localize(dateutil.parser.parse(request.args['start'])).astimezone(utc)
            self.end_dt = tz.localize(dateutil.parser.parse(request.args['end'])).astimezone(utc)
        except ParserError as e:
            raise BadRequest(str(e))

    def _process(self):
        query = (Event.query
                 .filter(Event.starts_between(self.start_dt, self.end_dt),
                         Event.is_visible_in(self.category.id),
                         ~Event.is_deleted)
                 .options(undefer(Event.detailed_category_chain),
                          selectinload('own_room'),
                          load_only('id', 'title', 'start_dt', 'end_dt', 'category_id', 'own_venue_id', 'own_room_id',
                                    'keywords')))
        events, categories, rooms, keywords, allowed_keywords = self._get_event_data(query)
        raw_locations = Location.query.options(load_only('id', 'name')).all()
        allow_keywords = bool(allowed_keywords)
        locations = [{'title': loc.name, 'id': loc.id} for loc in raw_locations]
        ongoing_events = (Event.query
                          .filter(Event.is_visible_in(self.category.id),
                                  ~Event.is_deleted,
                                  Event.start_dt < self.start_dt,
                                  Event.end_dt > self.end_dt)
                          .options(load_only('id', 'title', 'start_dt', 'end_dt', 'timezone'))
                          .order_by(Event.title)
                          .all())
        return jsonify_data(flash=False, events=events, categories=categories, locations=locations, rooms=rooms,
                            keywords=keywords, allow_keywords=allow_keywords,
                            group_by=self.group_by.name,
                            ongoing_event_count=len(ongoing_events),
                            ongoing_events_html=self._render_ongoing_events(ongoing_events))

    def _find_nearest_category(self, category_chain):
        for index, category_data in enumerate(category_chain):
            if category_data['id'] == self.category.id:
                if index == len(category_chain) - 1:
                    return category_data
                else:
                    return category_chain[index + 1]
        # this should never happen
        raise Exception(f'Category {self.category.id} not found in category chain')

    def _get_event_data(self, event_query):
        def calculate_keyword_id(kw):
            # we add 3 in order not to collide with special items with ids 0 and 1
            return crc32(kw) + 3

        data = []
        categories = {}
        rooms = {}
        keywords = {}
        allowed_keywords = global_event_settings.get('allowed_keywords')
        allowed_keywords_set = set(allowed_keywords)
        tz = self.category.display_tzinfo
        for event in event_query:
            valid_keywords = [keyword for keyword in event.keywords if keyword in allowed_keywords_set]
            for keyword in valid_keywords:
                keyword_id = calculate_keyword_id(keyword)
                if keyword_id not in keywords:
                    keywords.setdefault(keyword_id, {'id': keyword_id, 'title': keyword,
                                                     'color': f'#{generate_contrast_colors(keyword_id).background}'})
            category_data = self._find_nearest_category(event.detailed_category_chain)
            category_id = category_data['id']
            category_data['url'] = url_for('categories.calendar', category_id=category_id)
            room = event.room
            if room and room.id not in rooms:
                rooms[room.id] = {'id': room.id,
                                  'title': room.full_name,
                                  'venueId': room.location_id}
            event_data = {'title': event.title,
                          'start': event.start_dt.astimezone(tz).replace(tzinfo=None).isoformat(),
                          'end': event.end_dt.astimezone(tz).replace(tzinfo=None).isoformat(),
                          'url': event.url,
                          'categoryId': category_id,
                          'venueId': event.own_venue_id,
                          'keywords': event.keywords,
                          'validKeywords': valid_keywords,
                          'roomId': room.id if room else None}
            if self.group_by == self.GroupBy.category:
                colors = generate_contrast_colors(category_id)
            elif self.group_by == self.GroupBy.location:
                colors = generate_contrast_colors(event.own_venue_id or 0)
            elif self.group_by == self.GroupBy.room:
                colors = generate_contrast_colors(room.id if room else 0)
            else:
                # by keywords
                if not valid_keywords:
                    keyword_id = 0
                elif len(valid_keywords) > 1:
                    keyword_id = 1
                else:
                    # only one keyword
                    keyword_id = calculate_keyword_id(valid_keywords[0])
                event_data['keywordId'] = keyword_id
                colors = generate_contrast_colors(keyword_id)
            event_data.update({'textColor': f'#{colors.text}', 'color': f'#{colors.background}'})
            data.append(event_data)
            categories[category_id] = category_data
        return data, list(categories.values()), list(rooms.values()), list(keywords.values()), allowed_keywords

    def _render_ongoing_events(self, ongoing_events):
        template = get_template_module('categories/display/_calendar_ongoing_events.html')
        return template.render_ongoing_events(ongoing_events, self.category.display_tzinfo)


class RHCategoryUpcomingEvent(RHDisplayCategoryBase):
    """Redirect to the upcoming event of a category."""

    def _process(self):
        event = self._get_upcoming_event()
        if event:
            return redirect(event.url)
        else:
            flash(_('There are no upcoming events for this category'))
            return redirect(self.category.url)

    def _get_upcoming_event(self):
        query = (Event.query
                 .filter(Event.is_visible_in(self.category.id),
                         Event.start_dt > now_utc(),
                         ~Event.is_deleted)
                 .options(subqueryload('acl_entries'))
                 .order_by(Event.start_dt, Event.id))
        res = get_n_matching(query, 1, lambda event: event.can_access(session.user))
        if res:
            return res[0]
