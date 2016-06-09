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

from io import BytesIO
from math import ceil

from flask import jsonify, request, session
from sqlalchemy.orm import undefer
from werkzeug.exceptions import NotFound

from indico.modules.categories.controllers.base import RHDisplayCategoryBase
from indico.modules.categories.util import get_category_stats
from indico.modules.categories.views import WPCategoryStatistics
from indico.modules.users import User
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import send_file
from indico.web.util import jsonify_data
from MaKaC.conference import CategoryManager


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


def _serialize_category(category, include_breadcrumb=False):
    data = {
        'id': category.id,
        'title': category.title,
        'is_protected': category.is_protected,
        'category_count': category.deep_children_count,
        'event_count': category.deep_events_count,
        'can_access': category.can_access(session.user)
    }
    if include_breadcrumb:
        data['path'] = [{'id': c.id, 'title': c.title} for c in category.parent_chain_query]
    return data


class RHCategoryInfo(RHDisplayCategoryBase):
    def _process(self):
        category = self._target.as_new
        category_contents = category.children
        return jsonify_data(category=_serialize_category(category, include_breadcrumb=True),
                            subcategories=[_serialize_category(c) for c in category_contents])
