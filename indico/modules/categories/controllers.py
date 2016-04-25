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

from math import ceil

from flask import jsonify, request

from indico.modules.categories.util import get_category_stats
from indico.modules.categories.views import WPCategoryStatistics
from indico.modules.users import User
from indico.util.date_time import now_utc
from indico.util.i18n import _
from MaKaC.webinterface.rh.categoryDisplay import RHCategDisplayBase


def _plot_data(stats, tooltip=''):
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


def _process_stats(stats, root=False):
    # tooltip formatting is for ease of translation
    plots = [
        (_('Number of events'), _('The year is the one of the start date of the event.'),
         _plot_data(stats.get('events_by_year', {}),
                    tooltip=_('{value} events in {year}').format(value='', year=''))),
        (_('Number of contributions'), _('The year is the one of the start date of the contribution.'),
         _plot_data(stats.get('contribs_by_year', {}),
                    tooltip=_('{value} contributions in {year}').format(value='', year='')))
    ]
    values = [(_('Number of attachments'), stats['attachments'])]
    if root:
        values.append((_('Number of users'), _count_users()))

    return plots, values, stats['updated']


def _count_users():
    return User.find(is_deleted=False, is_pending=False).count()


class RHCategoryStatistics(RHCategDisplayBase):
    def _process(self):
        stats = get_category_stats(int(self._target.getId()))
        if request.accept_mimetypes.best_match(('application/json', 'text/html')) == 'application/json':
            data = {'events': stats['events_by_year'], 'contributions': stats['contribs_by_year'],
                    'files': stats['attachments'], 'updated': stats['updated'].isoformat()}
            if self._target.isRoot():
                data['users'] = _count_users()
            return jsonify(data)
        else:
            plots, values, updated = _process_stats(stats, root=self._target.isRoot())
            return WPCategoryStatistics.render_template('category_statistics.html', self._target,
                                                        cat=self._target,
                                                        plots=plots,
                                                        values=values,
                                                        updated=updated,
                                                        has_stats=True)
