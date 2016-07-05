# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from datetime import datetime, timedelta
from io import BytesIO
from itertools import groupby
from math import ceil
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from flask import jsonify, request, session
from sqlalchemy.orm import joinedload, load_only, subqueryload, undefer
from werkzeug.exceptions import BadRequest, NotFound

from indico.core.db import db
from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.categories.util import (get_category_stats, get_upcoming_events, serialize_category_atom,
                                            serialize_category_ical)
from indico.modules.categories.views import WPCategory, WPCategoryStatistics
from indico.modules.events.models.events import Event
from indico.modules.events.util import get_base_ical_parameters
from indico.modules.news.util import get_recent_news
from indico.modules.users import User
from indico.modules.users.models.favorites import favorite_category_table
from indico.util.date_time import format_date, now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data
from MaKaC.conference import CategoryManager
from MaKaC.webinterface.rh.base import RH


class RHCategoryIcon(RHDisplayCategoryBase):
    _category_query_options = undefer('icon'),

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
        return WPCategoryStatistics.render_template('category_statistics.html',
                                                    # TODO: use self.category once we don't use the legacy WP anymore
                                                    CategoryManager().getById(self.category.id, True),
                                                    cat=self.category, plots=plots, values=values, updated=updated,
                                                    has_stats=True)

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


def _serialize_category(category, with_favorite=False, with_path=False, parent_data=None):
    data = {
        'id': category.id,
        'title': category.title,
        'is_protected': category.is_protected,
        'has_events': category.has_events,
        'deep_category_count': category.deep_children_count,
        'deep_event_count': category.deep_events_count,
        'can_access': category.can_access(session.user),
    }
    if with_path:
        if parent_data and 'path' in parent_data:
            data['path'] = parent_data['path'][:]
            data['path'].append({'id': parent_data['id'], 'title': parent_data['title']})
        else:
            data['path'] = [{'id': c.id, 'title': c.title}
                            for c in category.parent_chain_query.options(load_only('id', 'title'))]
    if with_favorite:
        data['is_favorite'] = session.user and category in session.user.favorite_categories
    return data


class RHCategoryInfo(RHDisplayCategoryBase):
    @property
    def _category_query_options(self):
        children_strategy = joinedload('children')
        children_strategy.load_only('id', 'parent_id', 'title', 'protection_mode')
        children_strategy.subqueryload('acl_entries')
        children_strategy.undefer('deep_children_count')
        children_strategy.undefer('deep_events_count')
        children_strategy.undefer('has_events')
        return children_strategy, subqueryload('acl_entries'), load_only('id', 'parent_id', 'title', 'protection_mode',
                                                                         'has_events')

    def _process(self):
        category_data = _serialize_category(self.category, with_path=True)
        return jsonify_data(category=category_data,
                            subcategories=[_serialize_category(c, with_path=True, parent_data=category_data)
                                           for c in self.category.children],
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
        return jsonify_data(categories=[_serialize_category(c, with_favorite=True, with_path=True) for c in query],
                            total_count=total_count, flash=False)


class RHDisplayCategoryEventsBase(RHDisplayCategoryBase):
    """Base class for display pages displaying an event list"""

    _category_query_options = (joinedload('children').undefer('deep_events_count'), undefer('attachment_count'),
                               undefer('has_events'))

    def _checkParams(self):
        RHDisplayCategoryBase._checkParams(self)
        self.now = now_utc(exact=False).astimezone(self.category.display_tzinfo)

    def format_event_date(self, event):
        day_month = 'dd MMM'
        tzinfo = self.category.display_tzinfo
        start_dt = event.start_dt.astimezone(tzinfo)
        end_dt = event.end_dt.astimezone(tzinfo)
        if start_dt.year != end_dt.year:
            return '{} - {}'.format(format_date(start_dt, timezone=tzinfo), format_date(end_dt, timezone=tzinfo))
        elif (start_dt.month != end_dt.month) or (start_dt.day != end_dt.day):
            return '{} - {}'.format(format_date(start_dt, day_month, timezone=tzinfo),
                                    format_date(end_dt, day_month, timezone=tzinfo))
        else:
            return format_date(start_dt, day_month, timezone=tzinfo)

    def group_by_month(self, events):
        def _format_tuple(x):
            (year, month), events = x
            return {'name': format_date(datetime(year=year, month=month, day=1), format='MMMM Y'),
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
        past_threshold = self.now - relativedelta(months=1, day=1, hour=0, minute=0)
        future_threshold = self.now + relativedelta(months=1, day=1, hour=0, minute=0)
        event_query = (Event.query.with_parent(self.category)
                       .order_by(Event.start_dt.desc())
                       .options(joinedload('person_links'), load_only('id', 'category_id', 'created_dt', 'end_dt',
                                                                      'protection_mode', 'start_dt', 'title', 'type_')))
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
        params.update(get_base_ical_parameters(session.user, self.category, 'category',
                                               '/export/categ/{0}.ics'.format(self.category.id)))

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
                       .order_by(Event.start_dt.desc())
                       .options(joinedload('person_links')))
        if before:
            event_query = event_query.filter(Event.start_dt < before)
        if after:
            event_query = event_query.filter(Event.start_dt >= after + relativedelta(months=1))
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
        buf = serialize_category_ical(self.category, session.user, Event.end_dt >= (now_utc() - timedelta(weeks=4)))
        return send_file(filename, buf, 'text/calendar')


class RHExportCategoryAtom(RHDisplayCategoryBase):
    def _process(self):
        filename = '{}-category.atom'.format(secure_filename(self.category.title, str(self.category.id)))
        buf = serialize_category_atom(self.category,
                                      url_for(request.endpoint, self.category, _external=True),
                                      session.user,
                                      Event.end_dt >= now_utc())
        return send_file(filename, buf, 'application/atom+xml')
