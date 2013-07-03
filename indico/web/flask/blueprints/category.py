# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from indico.web.flask.util import rh_as_view, redirect_view
from indico.web.flask.wrappers import IndicoBlueprint


category = IndicoBlueprint('category', __name__, url_prefix='/category')


# Short URLs
category.add_url_rule('!/categ/<categId>', view_func=redirect_view('.categoryDisplay'), strict_slashes=False)
category.add_url_rule('!/c/<categId>', view_func=redirect_view('.categoryDisplay'), strict_slashes=False)

# Display
category.add_url_rule('/<categId>/', 'categoryDisplay', rh_as_view(categoryDisplay.RHCategoryDisplay))
category.add_url_rule('/<categId>/events.atom', 'categoryDisplay-atom', rh_as_view(categoryDisplay.RHCategoryToAtom))
category.add_url_rule('/<categId>/events.rss', 'categoryDisplay-rss', rh_as_view(categoryDisplay.RHCategoryToRSS))
category.add_url_rule('/<categId>/events.ics', 'categoryDisplay-ical', rh_as_view(categoryDisplay.RHCategoryToiCal))
category.add_url_rule('/<categId>/icon', 'categoryDisplay-getIcon', rh_as_view(categoryDisplay.RHCategoryGetIcon))
category.add_url_rule('/<categId>/statistics', 'categoryStatistics', rh_as_view(categoryDisplay.RHCategoryStatistics))

# Overview
category.add_url_rule('/<categId>/overview', 'categOverview', rh_as_view(categoryDisplay.RHCategOverviewDisplay))
category.add_url_rule('/<selCateg>/overview', 'categOverview', rh_as_view(categoryDisplay.RHCategOverviewDisplay))
category.add_url_rule('/overview', 'categOverview', rh_as_view(categoryDisplay.RHCategOverviewDisplay))
category.add_url_rule('/<categId>/overview.rss', 'categOverview-rss', rh_as_view(categoryDisplay.RHTodayCategoryToRSS))

# Event map
category.add_url_rule('/<categId>/map', 'categoryMap', rh_as_view(categoryDisplay.RHCategoryMap))

# Event calendar
category.add_url_rule('/calendar/', 'wcalendar', rh_as_view(calendar.RHCalendar))
category.add_url_rule('/calendar/select', 'wcalendar-select', rh_as_view(calendar.RHCalendarSelectCategories),
                      methods=('GET', 'POST'))
