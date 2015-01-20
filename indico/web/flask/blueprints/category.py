# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import calendar, categoryDisplay
from indico.web.flask.util import redirect_view
from indico.web.flask.wrappers import IndicoBlueprint


category = IndicoBlueprint('category', __name__, url_prefix='/category')


# Short URLs
category.add_url_rule('!/categ/<categId>', view_func=redirect_view('.categoryDisplay'), strict_slashes=False)
category.add_url_rule('!/c/<categId>', view_func=redirect_view('.categoryDisplay'), strict_slashes=False)

# Display
category.add_url_rule('/<categId>/', 'categoryDisplay', categoryDisplay.RHCategoryDisplay)
category.add_url_rule('/<categId>/events.atom', 'categoryDisplay-atom', categoryDisplay.RHCategoryToAtom)
category.add_url_rule('/<categId>/events.rss', 'categoryDisplay-rss', categoryDisplay.RHCategoryToRSS)
category.add_url_rule('/<categId>/events.ics', 'categoryDisplay-ical', categoryDisplay.RHCategoryToiCal)
category.add_url_rule('/<categId>/icon', 'categoryDisplay-getIcon', categoryDisplay.RHCategoryGetIcon)
category.add_url_rule('/<categId>/statistics', 'categoryStatistics', categoryDisplay.RHCategoryStatistics)

# Overview
category.add_url_rule('/<categId>/overview', 'categOverview', categoryDisplay.RHCategOverviewDisplay)
category.add_url_rule('/<selCateg>/overview', 'categOverview', categoryDisplay.RHCategOverviewDisplay)
category.add_url_rule('/overview', 'categOverview', categoryDisplay.RHCategOverviewDisplay)
category.add_url_rule('/<categId>/overview.rss', 'categOverview-rss', categoryDisplay.RHTodayCategoryToRSS)

# Event map
category.add_url_rule('/<categId>/map', 'categoryMap', categoryDisplay.RHCategoryMap)

# Event calendar
category.add_url_rule('/calendar/', 'wcalendar', calendar.RHCalendar)
category.add_url_rule('/calendar/select', 'wcalendar-select', calendar.RHCalendarSelectCategories,
                      methods=('GET', 'POST'))
