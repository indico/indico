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

import sys

from flask import jsonify, request

from indico.modules.categories.views import WPCategoryStatistics
from indico.util.date_time import now_utc
from indico.util.i18n import _
from MaKaC.statistics import CategoryStatistics
from MaKaC.webinterface.rh.categoryDisplay import RHCategDisplayBase


def _plot_data(stats, tooltip=''):
    years = sorted(stats.iterkeys())
    now = now_utc().year
    data = {}
    if years:
        year = min(now, years[0]) - 1
        max_year = max(now, years[-1])
        while year <= max_year:
            val = stats.get(year, 0)
            if not val and not any(stats.get(y, 0) for y in xrange(year, min(max_year, year + 10))):
                end = next((y - 1 for y in xrange(year, max_year) if stats.get(y, 0)), sys.maxint)
                year = end + 1
            else:
                data[year] = val
                year += 1
    return {'values': data, 'total': sum(data.itervalues()), 'label_x': _("Years"), 'label_y': '', 'tooltip': tooltip}


def _process_stats(stats, root=False):
    if stats is None:
        return

    # tooltip formatting is for ease of translation
    plots = [
        (_('Number of events'), _('The year is the one of the start date of the event.'),
         _plot_data(stats.get('events', {}),
                    tooltip=_('{value} events in {year}').format(value='', year=''))),
        (_('Number of contributions'), _('The year is the one of the start date of the contribution.'),
         _plot_data(stats.get('contributions', {}),
                    tooltip=_('{value} contributions in {year}').format(value='', year='')))
    ]
    values = [(_('Number of attachments'), stats['files'])]
    if root:
        values.append((_('Number of users'), stats.get('users', 0)))

    return plots, values, stats['updated']


class RHCategoryStatistics(RHCategDisplayBase):
    def _process(self):
        stats = CategoryStatistics(self._target).getStatistics().copy()
        if request.accept_mimetypes.best_match(('application/json', 'text/html')) == 'application/json':
            if stats is None:
                stats = {'events': None, 'contributions': None, 'files': None, 'updated': None}
            else:
                stats = dict(stats)

            if stats['updated']:
                stats['updated'] = stats['updated'].isoformat()
            return jsonify(stats)
        else:
            plots, values, updated = _process_stats(stats, root=self._target.isRoot())
            return WPCategoryStatistics.render_template('category_statistics.html', self._target,
                                                        cat=self._target,
                                                        plots=plots,
                                                        values=values,
                                                        updated=updated)
