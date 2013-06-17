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

from flask import Blueprint
import MaKaC.webinterface.rh.calendar as calendar
import MaKaC.webinterface.rh.categoryDisplay as categoryDisplay
from indico.web.flask.util import rh_as_view


category = Blueprint('category', __name__, url_prefix='/category')
# categoryDisplay.py
category.add_url_rule('/<categId>/', 'categoryDisplay', rh_as_view(categoryDisplay.RHCategoryDisplay))
category.add_url_rule('/<categId>/events.atom', 'categoryDisplay-atom', rh_as_view(categoryDisplay.RHCategoryToAtom))
category.add_url_rule('/<categId>/events.rss', 'categoryDisplay-rss', rh_as_view(categoryDisplay.RHCategoryToRSS))
category.add_url_rule('/<categId>/events.ics', 'categoryDisplay-ical', rh_as_view(categoryDisplay.RHCategoryToiCal))
category.add_url_rule('/<categId>/icon', 'categoryDisplay-getIcon', rh_as_view(categoryDisplay.RHCategoryGetIcon))
# categOverview.py
category.add_url_rule('/<categId>/overview', 'categOverview', rh_as_view(categoryDisplay.RHCategOverviewDisplay))
category.add_url_rule('/<selCateg>/overview', 'categOverview', rh_as_view(categoryDisplay.RHCategOverviewDisplay))
category.add_url_rule('/overview', 'categOverview', rh_as_view(categoryDisplay.RHCategOverviewDisplay))
category.add_url_rule('/<categId>/overview.rss', 'categOverview-rss', rh_as_view(categoryDisplay.RHTodayCategoryToRSS))
# categoryMap.py
category.add_url_rule('/<categId>/map', 'categoryMap', rh_as_view(categoryDisplay.RHCategoryMap))
# categoryStatistics.py
category.add_url_rule('/<categId>/statistics', 'categoryStatistics', rh_as_view(categoryDisplay.RHCategoryStatistics))
# wcalendar.py
category.add_url_rule('/calendar/', 'wcalendar', rh_as_view(calendar.RHCalendar))
category.add_url_rule('/calendar/select', 'wcalendar-select', rh_as_view(calendar.RHCalendarSelectCategories),
                      methods=('GET', 'POST'))
