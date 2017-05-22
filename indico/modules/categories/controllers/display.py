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

from datetime import date, datetime, time, timedelta
from functools import partial
from io import BytesIO
from itertools import chain, groupby, imap
from math import ceil
from operator import attrgetter, itemgetter
from time import mktime

import dateutil
from dateutil.relativedelta import relativedelta
from flask import Response, jsonify, request, session
from pytz import utc
from sqlalchemy.orm import joinedload, load_only, subqueryload, undefer, undefer_group
from werkzeug.exceptions import BadRequest, NotFound

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.legacy.webinterface.rh.base import RH
from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.categories.legacy import XMLCategorySerializer
from indico.modules.categories.models.categories import Category
from indico.modules.categories.serialize import (serialize_categories_ical, serialize_category, serialize_category_atom,
                                                 serialize_category_chain)
from indico.modules.categories.util import get_category_stats, get_upcoming_events
from indico.modules.categories.views import WPCategory, WPCategoryStatistics
from indico.modules.events.models.events import Event
from indico.modules.events.timetable.util import get_category_timetable
from indico.modules.events.util import get_base_ical_parameters
from indico.modules.news.util import get_recent_news
from indico.modules.users import User
from indico.modules.users.models.favorites import favorite_category_table
from indico.util.date_time import format_date, format_number, now_utc
from indico.util.decorators import classproperty
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data


CALENDAR_COLOR_PALETTE = [
    ColorTuple('#1F1100', '#ECC495'),
    ColorTuple('#0F0202', '#B9CBCA'),
    ColorTuple('#0D1E1F', '#C2ECEF'),
    ColorTuple('#000000', '#D0C296'),
    ColorTuple('#202020', '#EFEBC2')
]


def _flat_map(func, list_):
    return chain.from_iterable(imap(func, list_))


class RHCategoryIcon(RHDisplayCategoryBase):
    _category_query_options = undefer('icon'),

    def _checkProtection(self):
        # Category icons are always public
        pass

    def _process(self):
        if not self.category.has_icon:
            raise NotFound
        metadata = self.category.icon_metadata
        return send_file(metadata['filename'], BytesIO(self.category.icon), mimetype=metadata['content_type'],
                         conditional=True)


class RHCategoryLogo(RHDisplayCategoryBase):
    _category_query_options = undefer('logo'),

    def _process(self):
        if not self.category.has_logo:
            raise NotFound
        metadata = self.category.logo_metadata
        return send_file(metadata['filename'], BytesIO(self.category.logo), mimetype=metadata['content_type'],
                         conditional=True)


class RHCategoryStatistics(RHDisplayCategoryBase):
    def _get_stats_json(self, stats):
        data = {'events': stats['events_by_year'], 'contributions': stats['contribs_by_year'],
                'files': stats['attachments'], 'updated': stats['updated'].isoformat()}
        if self.category.is_root:
            data['users'] = self._count_users()
        return jsonify(data)

    def _get_stats_html(self, stats):
        plots, values, updated = self._process_stats(stats, root=self.category.is_root)
        return WPCategoryStatistics.render_template('category_statistics.html', self.category,
                                                    plots=plots, values=values, updated=updated, has_stats=True)

    def _process(self):
        stats = get_category_stats(self.category.id)
        if request.accept_mimetypes.best_match(('application/json', 'text/html')) == 'application/json':
            return self._get_stats_json(stats)
        else:
            return self._get_stats_html(stats)

    def _plot_data(self, stats, tooltip=''):
        years = sorted(stats.iterkeys())
        min_year = now_utc().year
        max_year = min_year
        if years:
            min_year = min(min_year, years[0]) - 1
            max_year = max(max_year, years[-1])
            data = {year: stats.get(year, 0) for year in xrange(min_year, max_year + 1)}
            max_y = ceil(max(data.itervalues()) * 1.1)  # 1.1 for padding in the graph
        else:
            data = {}
            max_y = 0
        return {'min_x': min_year, 'max_x': max_year, 'min_y': 0, 'max_y': max_y, 'values': data,
                'total': sum(data.itervalues()), 'label_x': _("Years"), 'label_y': '', 'tooltip': tooltip}

    def _process_stats(self, stats, root=False):
        # tooltip formatting is for ease of translation
        plots = [(_('Number of events'),
                  _('The year is the one of the start date of the event.'),
                  self._plot_data(stats.get('events_by_year', {}),
                                  tooltip=_('{value} events in {year}').format(value='', year=''))),
                 (_('Number of contributions'),
                  _('The year is the one of the start date of the contribution.'),
                  self._plot_data(stats.get('contribs_by_year', {}),
                                  tooltip=_('{value} contributions in {year}').format(value='', year='')))]
        values = [(_('Number of attachments'), stats['attachments'])]
        if root:
            values.append((_('Number of users'), self._count_users()))
        return plots, values, stats['updated']

    def _count_users(self):
        return User.find(is_deleted=False, is_pending=False).count()


class RHCategoryInfo(RHDisplayCategoryBase):
    @classproperty
    @classmethod
    def _category_query_options(cls):
        children_strategy = subqueryload('children')
        children_strategy.load_only('id', 'parent_id', 'title', 'protection_mode')
        children_strategy.subqueryload('acl_entries')
        children_strategy.undefer('deep_children_count')
        children_strategy.undefer('deep_events_count')
        children_strategy.undefer('has_events')
        return (children_strategy,
                load_only('id', 'parent_id', 'title', 'protection_mode'),
                subqueryload('acl_entries'),
                undefer('deep_children_count'),
                undefer('deep_events_count'),
                undefer('has_events'),
                undefer('chain'))

    def _process(self):
        return jsonify_data(flash=False,
                            **serialize_category_chain(self.category, include_children=True, include_parents=True))


class RHReachableCategoriesInfo(RH):
    def _get_reachable_categories(self, id_, excluded_ids):
        cat = Category.query.filter_by(id=id_).options(joinedload('children').load_only('id')).one()
        ids = ({c.id for c in cat.children} | {c.id for c in cat.parent_chain_query}) - excluded_ids
        if not ids:
            return []
        return (Category.query
                .filter(Category.id.in_(ids))
                .options(*RHCategoryInfo._category_query_options)
                .all())

    def _process(self):
        excluded_ids = set(request.json.get('exclude', set())) if request.json else set()
        categories = self._get_reachable_categories(request.view_args['category_id'], excluded_ids=excluded_ids)
        return jsonify_data(categories=[serialize_category_chain(c, include_children=True) for c in categories],
                            flash=False)


class RHCategorySearch(RH):
    def _process(self):
        q = request.args['q'].lower()
        query = (Category.query
                 .filter(Category.title_matches(q))
                 .options(undefer('deep_children_count'), undefer('deep_events_count'), undefer('has_events'),
                          joinedload('acl_entries')))
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
    """Base class for display pages displaying an event list"""

    _category_query_options = (joinedload('children').load_only('id', 'title', 'protection_mode'),
                               undefer('attachment_count'), undefer('has_events'))
    _event_query_options = (joinedload('person_links'), joinedload('series'), undefer_group('series'),
                            load_only('id', 'category_id', 'created_dt', 'end_dt', 'protection_mode', 'start_dt',
                                      'title', 'type_', 'series_pos', 'series_count'))

    def _checkParams(self):
        RHDisplayCategoryBase._checkParams(self)
        self.now = now_utc(exact=False).astimezone(self.category.display_tzinfo)

    def format_event_date(self, event):
        day_month = 'dd MMM'
        tzinfo = self.category.display_tzinfo
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

    def group_by_month(self, events):
        def _format_tuple(x):
            (year, month), events = x
            return {'name': format_date(date(year, month, 1), format='MMMM yyyy'),
                    'events': list(events),
                    'is_current': year == self.now.year and month == self.now.month}

        def _key(event):
            start_dt = event.start_dt.astimezone(self.category.tzinfo)
            return start_dt.year, start_dt.month

        months = groupby(events, key=_key)
        return map(_format_tuple, months)

    def happening_now(self, event):
        return event.start_dt <= self.now < event.end_dt

    def is_recent(self, dt):
        return dt > self.now - relativedelta(weeks=1)


class RHDisplayCategory(RHDisplayCategoryEventsBase):
    """Show the contents of a category (events/subcategories)"""

    def _process(self):
        # Current events, which are always shown by default are events of this month and of the previous month.
        # If there are no events in this range, it will include the last and next month containing events.
        past_threshold = self.now - relativedelta(months=1, day=1, hour=0, minute=0)
        future_threshold = self.now + relativedelta(months=1, day=1, hour=0, minute=0)
        next_event_start_dt = (db.session.query(Event.start_dt)
                               .filter(Event.start_dt >= self.now, Event.category_id == self.category.id)
                               .order_by(Event.start_dt.asc())
                               .first() or (None,))[0]
        previous_event_start_dt = (db.session.query(Event.start_dt)
                                   .filter(Event.start_dt < self.now, Event.category_id == self.category.id)
                                   .order_by(Event.start_dt.desc())
                                   .first() or (None,))[0]
        if next_event_start_dt is not None and next_event_start_dt > future_threshold:
            future_threshold = next_event_start_dt + relativedelta(months=1, day=1, hour=0, minute=0)
        if previous_event_start_dt is not None and previous_event_start_dt < past_threshold:
            past_threshold = previous_event_start_dt.replace(day=1, hour=0, minute=0)
        event_query = (Event.query.with_parent(self.category)
                       .options(*self._event_query_options)
                       .order_by(Event.start_dt.desc()))
        past_event_query = event_query.filter(Event.start_dt < past_threshold)
        future_event_query = event_query.filter(Event.start_dt >= future_threshold)
        current_event_query = event_query.filter(Event.start_dt >= past_threshold,
                                                 Event.start_dt < future_threshold)
        events = current_event_query.filter(Event.start_dt < future_threshold).all()
        events_by_month = self.group_by_month(events)

        future_event_count = future_event_query.count()
        past_event_count = past_event_query.count()

        show_past_events = bool(self.category.id in session.get('fetch_past_events_in', set()) or
                                (session.user and session.user.settings.get('show_past_events', False)))

        managers = sorted(self.category.get_manager_list(), key=attrgetter('principal_type.name', 'name'))

        threshold_format = '%Y-%m'
        params = {'event_count': len(events),
                  'events_by_month': events_by_month,
                  'format_event_date': self.format_event_date,
                  'future_event_count': future_event_count,
                  'future_threshold': future_threshold.strftime(threshold_format),
                  'happening_now': self.happening_now,
                  'is_recent': self.is_recent,
                  'managers': managers,
                  'past_event_count': past_event_count,
                  'show_past_events': show_past_events,
                  'past_threshold': past_threshold.strftime(threshold_format),
                  'atom_feed_url': url_for('.export_atom', self.category),
                  'atom_feed_title': _('Events of "{}"').format(self.category.title)}
        params.update(get_base_ical_parameters(session.user, 'category',
                                               '/export/categ/{0}.ics'.format(self.category.id), {'from': '-31d'}))

        if not self.category.is_root:
            return WPCategory.render_template('display/category.html', self.category, **params)

        news = get_recent_news()
        upcoming_events = get_upcoming_events()
        return WPCategory.render_template('display/root_category.html', self.category, news=news,
                                          upcoming_events=upcoming_events, **params)


class RHEventList(RHDisplayCategoryEventsBase):
    """Return the HTML for the event list before/after a specific month"""

    def _parse_year_month(self, string):
        try:
            dt = datetime.strptime(string, '%Y-%m')
        except (TypeError, ValueError):
            return None
        return self.category.display_tzinfo.localize(dt)

    def _checkParams(self):
        RHDisplayCategoryEventsBase._checkParams(self)
        before = self._parse_year_month(request.args.get('before'))
        after = self._parse_year_month(request.args.get('after'))
        if before is None and after is None:
            raise BadRequest('"before" or "after" parameter must be specified')
        event_query = (Event.query.with_parent(self.category)
                       .options(*self._event_query_options)
                       .order_by(Event.start_dt.desc()))
        if before:
            event_query = event_query.filter(Event.start_dt < before)
        if after:
            event_query = event_query.filter(Event.start_dt >= after)
        self.events = event_query.all()

    def _process(self):
        events_by_month = self.group_by_month(self.events)
        tpl = get_template_module('categories/display/event_list.html')
        html = tpl.event_list_block(events_by_month=events_by_month, format_event_date=self.format_event_date,
                                    is_recent=self.is_recent, happening_now=self.happening_now)
        return jsonify_data(flash=False, html=html)


class RHShowPastEventsInCategory(RHDisplayCategoryBase):
    """Set whether the past events in a category are automatically displayed or not"""

    def _show_past_events(self, show_past_events):
        category_ids = session.setdefault('fetch_past_events_in', set())
        if show_past_events:
            category_ids.add(self.category.id)
        else:
            category_ids.discard(self.category.id)
        session.modified = True

    def _process_DELETE(self):
        self._show_past_events(False)

    def _process_PUT(self):
        self._show_past_events(True)


class RHExportCategoryICAL(RHDisplayCategoryBase):
    def _process(self):
        filename = '{}-category.ics'.format(secure_filename(self.category.title, str(self.category.id)))
        buf = serialize_categories_ical([self.category.id], session.user,
                                        Event.end_dt >= (now_utc() - timedelta(weeks=4)))
        return send_file(filename, buf, 'text/calendar')


class RHExportCategoryAtom(RHDisplayCategoryBase):
    def _process(self):
        filename = '{}-category.atom'.format(secure_filename(self.category.title, str(self.category.id)))
        buf = serialize_category_atom(self.category,
                                      url_for(request.endpoint, self.category, _external=True),
                                      session.user,
                                      Event.end_dt >= now_utc())
        return send_file(filename, buf, 'application/atom+xml')


class RHXMLExportCategoryInfo(RH):
    def _checkParams(self):
        try:
            id_ = int(request.args['id'])
        except ValueError:
            raise BadRequest('Invalid Category ID')
        self.category = Category.get_one(id_, is_deleted=False)

    def _process(self):
        category_xml_info = XMLCategorySerializer(self.category).serialize_category()
        return Response(category_xml_info, mimetype='text/xml')


class RHCategoryOverview(RHDisplayCategoryBase):
    """Display the events for a particular day, week or month"""

    def _checkParams(self):
        RHDisplayCategoryBase._checkParams(self)
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
        info = get_category_timetable([self.category.id], self.start_dt, self.end_dt, detail_level=self.detail,
                                      tz=self.category.display_tzinfo, from_categ=self.category, grouped=False)
        events = info['events']

        # Only categories with icons are listed in the sidebar
        subcategory_ids = {event.category.effective_icon_data['source_id']
                           for event in events if event.category.has_effective_icon}
        subcategories = Category.query.filter(Category.id.in_(subcategory_ids))

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

        events_by_day = []
        for day in days:
            events_by_day.append((day, self._pop_head_while(lambda x: x.start_dt.date() <= day.date(), events)))

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
        timetable_objects = sorted(chain(*info[event.id].values()), key=attrgetter('timetable_entry.start_dt'))
        timetable_objects_by_date = {x[0]: list(x[1]) for x
                                     in groupby(timetable_objects, key=lambda x: x.start_dt.astimezone(tzinfo).date())}

        # All the days of the event shown in the overview
        event_days = self._get_days(max(self.start_dt, event.start_dt.astimezone(tzinfo)),
                                    min(self.end_dt, event.end_dt.astimezone(tzinfo)))

        # Generate a proxy object with adjusted start_dt and timetable_objects for each day
        return [_EventProxy(event, day, tzinfo, timetable_objects_by_date.get(day.date(), [])) for day in event_days]


class _EventProxy(object):
    def __init__(self, event, date, tzinfo, timetable_objects):
        start_dt = datetime.combine(date, event.start_dt.astimezone(tzinfo).timetz())
        assert date >= event.start_dt
        assert date <= event.end_dt
        object.__setattr__(self, '_start_dt', start_dt)
        object.__setattr__(self, '_real_event', event)
        object.__setattr__(self, '_timetable_objects', timetable_objects)

    def __getattribute__(self, name):
        if name == 'start_dt':
            return object.__getattribute__(self, '_start_dt')
        event = object.__getattribute__(self, '_real_event')
        if name == 'timetable_objects':
            return object.__getattribute__(self, '_timetable_objects')
        if name == 'ongoing':
            return event.start_dt.date() != self.start_dt.date()
        if name == 'first_occurence_start_dt':
            return event.start_dt
        return getattr(event, name)

    def __setattr__(self, name, value):
        raise AttributeError('This instance is read-only')

    def __repr__(self):
        return '<_EventProxy({}, {})>'.format(self.start_dt, object.__getattribute__(self, '_real_event'))


class RHCategoryCalendarView(RHDisplayCategoryBase):
    def _process(self):
        if not request.is_xhr:
            return WPCategory.render_template('display/calendar.html', self.category,
                                              start_dt=request.args.get('start_dt'))
        tz = self.category.display_tzinfo
        start = tz.localize(dateutil.parser.parse(request.args['start'])).astimezone(utc)
        end = tz.localize(dateutil.parser.parse(request.args['end'])).astimezone(utc)
        query = (Event.query
                 .filter(Event.starts_between(start, end),
                         Event.is_visible_in(self.category),
                         ~Event.is_deleted)
                 .options(load_only('id', 'title', 'start_dt', 'end_dt', 'category_id')))
        events = self._get_event_data(query)
        ongoing_events = (Event.query
                          .filter(Event.is_visible_in(self.category),
                                  Event.start_dt < start,
                                  Event.end_dt > end)
                          .options(load_only('id', 'title', 'start_dt', 'end_dt', 'timezone'))
                          .order_by(Event.title)
                          .all())
        return jsonify_data(flash=False, events=events, ongoing_event_count=len(ongoing_events),
                            ongoing_events_html=self._render_ongoing_events(ongoing_events))

    def _get_event_data(self, event_query):
        data = []
        tz = self.category.display_tzinfo
        for event in event_query:
            category_id = event.category_id
            event_data = {'title': event.title,
                          'start': event.start_dt.astimezone(tz).replace(tzinfo=None).isoformat(),
                          'end': event.end_dt.astimezone(tz).replace(tzinfo=None).isoformat(),
                          'url': event.url}
            colors = CALENDAR_COLOR_PALETTE[category_id % len(CALENDAR_COLOR_PALETTE)]
            event_data.update({'textColor': '#' + colors.text, 'color': '#' + colors.background})
            data.append(event_data)
        return data

    def _render_ongoing_events(self, ongoing_events):
        template = get_template_module('categories/display/_calendar_ongoing_events.html')
        return template.render_ongoing_events(ongoing_events, self.category.display_tzinfo)
