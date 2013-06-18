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

from flask import Blueprint, redirect, url_for
import MaKaC.webinterface.rh.calendar as calendar
import MaKaC.webinterface.rh.categoryDisplay as categoryDisplay
import MaKaC.webinterface.rh.categoryMod as categoryMod
from indico.web.flask.util import rh_as_view


category = Blueprint('category', __name__, url_prefix='/category')
category_shorturl = Blueprint('category_shorturl', __name__, url_prefix='/categ')


@category_shorturl.route('/<categId>', strict_slashes=False)
def shorturl(categId):
    return redirect(url_for('category.categoryDisplay', categId=categId))


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


# categoryModification.py
category.add_url_rule('/<categId>/modify/', 'categoryModification', rh_as_view(categoryMod.RHCategoryModification))
category.add_url_rule('/<categId>/modify/events', 'categoryModification-actionConferences',
                      rh_as_view(categoryMod.RHCategoryActionConferences), methods=('GET', 'POST'))
category.add_url_rule('/<categId>/modify/subcategories', 'categoryModification-actionSubCategs',
                      rh_as_view(categoryMod.RHCategoryActionSubCategs), methods=('GET', 'POST'))
category.add_url_rule('/<categId>/modify/clear-cache', 'categoryModification-clearCache',
                      rh_as_view(categoryMod.RHCategoryClearCache), methods=('POST',))
category.add_url_rule('/<categId>/modify/clear-event-cache', 'categoryModification-clearConferenceCaches',
                      rh_as_view(categoryMod.RHCategoryClearConferenceCaches), methods=('POST',))
# categoryAC.py
category.add_url_rule('/<categId>/modify/access', 'categoryAC', rh_as_view(categoryMod.RHCategoryAC))
category.add_url_rule('/<categId>/modify/access/visibility', 'categoryAC-setVisibility',
                      rh_as_view(categoryMod.RHCategorySetVisibility), methods=('POST',))
# categoryConfCreationControl.py
category.add_url_rule('/<categId>/modify/create-control', 'categoryConfCreationControl-setCreateConferenceControl',
                      rh_as_view(categoryMod.RHCategorySetConfControl), methods=('POST',))
category.add_url_rule('/<categId>/modify/notify-creation', 'categoryConfCreationControl-setNotifyCreation',
                      rh_as_view(categoryMod.RHCategorySetNotifyCreation), methods=('POST',))
# categoryTools.py
category.add_url_rule('/<categId>/modify/tools', 'categoryTools', rh_as_view(categoryMod.RHCategoryTools))
category.add_url_rule('/<categId>/delete', 'categoryTools-delete', rh_as_view(categoryMod.RHCategoryDeletion),
                      methods=('GET', 'POST'))
# categoryDataModification.py
category.add_url_rule('/<categId>/modify/data', 'categoryDataModification', rh_as_view(categoryMod.RHCategoryDataModif),
                      methods=('GET', 'POST'))
category.add_url_rule('/<categId>/modify/data/save', 'categoryDataModification-modify',
                      rh_as_view(categoryMod.RHCategoryPerformModification), methods=('POST',))
category.add_url_rule('/<categId>/modify/tasks', 'categoryDataModification-tasksOption',
                      rh_as_view(categoryMod.RHCategoryTaskOption), methods=('GET', 'POST'))
# Routes for categoryFiles.py
category.add_url_rule('/<categId>/modify/files', 'categoryFiles', rh_as_view(categoryMod.RHCategoryFiles))
category.add_url_rule('/<categId>/modify/files/add', 'categoryFiles-addMaterial', rh_as_view(categoryMod.RHAddMaterial),
                      methods=('POST',))
# Routes for categoryTasks.py
category.add_url_rule('/<categId>/tasks', 'categoryTasks', rh_as_view(categoryMod.RHCategoryTasks),
                      methods=('GET', 'POST'))
category.add_url_rule('/<categId>/tasks/action', 'categoryTasks-taskAction',
                      rh_as_view(categoryMod.RHCategoryTasksAction), methods=('GET', 'POST'))


# categoryCreation.py
category.add_url_rule('/<categId>/create/subcategory', 'categoryCreation', rh_as_view(categoryMod.RHCategoryCreation),
                      methods=('GET', 'POST'))
category.add_url_rule('/<categId>/create/subcategory/save', 'categoryCreation-create',
                      rh_as_view(categoryMod.RHCategoryPerformCreation), methods=('POST',))
