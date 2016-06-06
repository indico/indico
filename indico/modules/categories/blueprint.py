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

from indico.modules.categories.controllers.display import RHDisplayCategory, RHCategoryStatistics
from indico.modules.categories.controllers.management import RHCategorySettings
from indico.web.flask.util import redirect_view, make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint

from MaKaC.webinterface.rh import calendar, categoryDisplay

_bp = IndicoBlueprint('categories', __name__, template_folder='templates', url_prefix='/category/<int:category_id>')

_bp.add_url_rule('/manage/settings', 'manage', RHCategorySettings)
#_bp.add_url_rule('/', 'display', RHDisplayCategory)
_bp.add_url_rule('/', 'display', categoryDisplay.RHCategoryDisplay)

_legacy_bp = IndicoBlueprint('category', __name__, template_folder='templates',
                             url_prefix='/category/<int:categId>')

# Short URLs
_legacy_bp.add_url_rule('!/categ/<categId>', view_func=redirect_view('.display'), strict_slashes=False)
_legacy_bp.add_url_rule('!/c/<categId>', view_func=redirect_view('.display'), strict_slashes=False)

# Display
_legacy_bp.add_url_rule('/', 'categoryDisplay', categoryDisplay.RHCategoryDisplay)
_legacy_bp.add_url_rule('/statistics/', 'statistics', RHCategoryStatistics)
_legacy_bp.add_url_rule('/events.atom', 'categoryDisplay-atom', categoryDisplay.RHCategoryToAtom)
_legacy_bp.add_url_rule('/events.rss', 'categoryDisplay-rss',
                 make_compat_redirect_func(_legacy_bp, 'categoryDisplay-atom'))
_legacy_bp.add_url_rule('/events.ics', 'categoryDisplay-ical', categoryDisplay.RHCategoryToiCal)
_legacy_bp.add_url_rule('/icon', 'categoryDisplay-getIcon', categoryDisplay.RHCategoryGetIcon)

# Overview
_legacy_bp.add_url_rule('/overview', 'categOverview', categoryDisplay.RHCategOverviewDisplay)
_legacy_bp.add_url_rule('!/category/<selCateg>/overview', 'categOverview', categoryDisplay.RHCategOverviewDisplay)
_legacy_bp.add_url_rule('/overview', 'categOverview', categoryDisplay.RHCategOverviewDisplay)
_legacy_bp.add_url_rule('/overview.rss', 'categOverview-rss',
                 make_compat_redirect_func(_legacy_bp, 'categoryDisplay-atom'))

# Event map
_legacy_bp.add_url_rule('/map', 'categoryMap', categoryDisplay.RHCategoryMap)

# Event calendar
_legacy_bp.add_url_rule('!/category/calendar/', 'wcalendar', calendar.RHCalendar)
_legacy_bp.add_url_rule('!/category/calendar/select', 'wcalendar-select', calendar.RHCalendarSelectCategories,
                 methods=('GET', 'POST'))
