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

from datetime import timedelta
from io import BytesIO
from math import ceil
from operator import attrgetter

from flask import jsonify, request, session
from sqlalchemy.orm import subqueryload, load_only
from werkzeug.exceptions import NotFound
from sqlalchemy.orm import joinedload, undefer

from indico.core.db import db
from indico.modules import ModuleHolder
from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.categories.models.categories import Category
from indico.modules.categories.util import get_category_stats, serialize_category_ical
from indico.modules.categories.views import WPCategory, WPCategoryStatistics
from indico.modules.events.models.events import Event
from indico.modules.events.util import get_base_ical_parameters
from indico.modules.users import User
from indico.modules.users.models.favorites import favorite_category_table
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.web.flask.util import send_file
from indico.web.util import jsonify_data
from MaKaC.common.info import HelperMaKaCInfo
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


def _serialize_category(category, with_path=False, with_favorite=False):
    data = {
        'id': category.id,
        'title': category.title,
        'is_protected': category.is_protected,
        'event_count': category.event_count,
        'deep_category_count': category.deep_children_count,
        'deep_event_count': category.deep_events_count,
        'can_access': category.can_access(session.user),
    }
    if with_path:
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
        children_strategy.undefer('event_count')
        return children_strategy, subqueryload('acl_entries'), load_only('id', 'parent_id', 'title', 'protection_mode')

    def _process(self):
        return jsonify_data(category=_serialize_category(self.category, with_path=True),
                            subcategories=[_serialize_category(c) for c in self.category.children], flash=False)


class RHCategorySearch(RH):
    def _process(self):
        q = request.args['q'].lower()
        query = (Category.query
                 .filter(Category.title_matches(q))
                 .options(undefer('deep_children_count'), undefer('deep_events_count'), undefer('event_count'),
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
        return jsonify_data(categories=[_serialize_category(c, with_path=True, with_favorite=True) for c in query],
                            total_count=total_count, flash=False)


class RHDisplayCategory(RHDisplayCategoryBase):
    def _process(self):
        future_events = []
        past_events = []
        events = self.category.events

        if HelperMaKaCInfo.getMaKaCInfoInstance().isNewsActive():
            news_list = [{'title': x.getTitle(), 'creation_dt': x.getCreationDate()} for x
                         in ModuleHolder().getById('news').getNewsItemsList()[:2]]
        else:
            news_list = []

        legacy_upcoming_events = ModuleHolder().getById('upcoming_events').getUpcomingEventList()
        upcoming_events = [{'status': status,
                            'start_dt': start_or_end_dt if not status == 'ongoing' else None,
                            'end_dt': start_or_end_dt if status == 'ongoing' else None,
                            'title': title,
                            'id': event_id}
                           for status, start_or_end_dt, title, event_id in legacy_upcoming_events]

        managers = sorted(self.category.get_manager_list(), key=attrgetter('principal_type.name', 'name'))

        return WPCategory.render_template('display/category.html', self.category, events=events, managers=managers,
                                          news_list=news_list, upcoming_events=upcoming_events,
                                          **get_base_ical_parameters(session.user, self.category, 'category',
                                                                     '/export/categ/{0}.ics'.format(self.category.id)))


class RHExportCategoryICAL(RHDisplayCategoryBase):
    def _process(self):
        filename = '{}-category.ics'.format(secure_filename(self.category.title, str(self.category.id)))
        buf = serialize_category_ical(self.category, session.user, Event.end_dt >= (now_utc() - timedelta(weeks=4)))
        return send_file(filename, buf, 'text/calendar')
