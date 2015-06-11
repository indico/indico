# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import jsonify, request

from indico.modules.categories.views import WPCategoryStatistics
from indico.util.date_time import now_utc
from indico.util.i18n import _
from MaKaC.statistics import CategoryStatistics
from MaKaC.webinterface.rh.categoryDisplay import RHCategDisplayBase


def _plot_data(stats):
    years = sorted(stats.iterkeys())
    min_year = now_utc().year
    max_year = min_year + 1
    if years:
        min_year = min(min_year, years[0])
        max_year = max(max_year, years[-1])
        data = {year: stats.get(year, 0) for year in xrange(min_year, max_year + 1)}
    else:
        data = []
    return {'min_year': min_year, 'max_year': max_year, 'stats': data.items(),
            'max_val': max(data.itervalues()), 'total': sum(data.itervalues())}


def _process_stats(stats, root=False):
    if stats is None:
        return

    plots = [
        (_('Number of events'), _plot_data(stats.get('events', {}))),  # tag: events
        (_('Number of contributions'), _plot_data(stats.get('contributions', {})))  # tag contributions
    ]
    values = [
        stats['resources'],  # title Number of attachments
        stats.get('users') if root else None  # else _('No statistics for the users')
    ]
    updated = stats['updated'].strftime('%d %B %Y %H:%M')
    return plots, values, updated


class RHCategoryStatistics(RHCategDisplayBase):
    def _process(self):
        stats = CategoryStatistics(self._target).getStatistics()
        if request.accept_mimetypes.best_match(('application/json', 'text/html')) == 'application/json':
            if stats is None:
                stats = {'events': None, 'contributions': None, 'resources': None, 'updated': None}
            else:
                stats = dict(stats)

            if stats['updated']:
                stats['updated'] = stats['updated'].strftime("%d %B %Y %H:%M")
            return jsonify(stats)
        else:
            plots, values, updated = _process_stats(stats, root=self._target.isRoot())
            return WPCategoryStatistics.render_template('category_statistics.html', self._target,
                                                        cat=self._target,
                                                        plots=plots,
                                                        values=values,
                                                        updated=updated)
