# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import redirect, request

from indico.modules.categories.compat import compat_category
from indico.modules.categories.controllers.admin import RHManageUpcomingEvents
from indico.modules.categories.controllers.display import (RHCategoryCalendarView, RHCategoryIcon, RHCategoryInfo,
                                                           RHCategoryLogo, RHCategoryOverview, RHCategorySearch,
                                                           RHCategoryStatistics, RHDisplayCategory, RHEventList,
                                                           RHExportCategoryAtom, RHExportCategoryICAL,
                                                           RHReachableCategoriesInfo, RHShowFutureEventsInCategory,
                                                           RHShowPastEventsInCategory, RHSubcatInfo,
                                                           RHXMLExportCategoryInfo)
from indico.modules.categories.controllers.management import (RHCreateCategory, RHDeleteCategory, RHDeleteEvents,
                                                              RHDeleteSubcategories, RHManageCategoryContent,
                                                              RHManageCategoryIcon, RHManageCategoryLogo,
                                                              RHManageCategoryProtection, RHManageCategorySettings,
                                                              RHMoveCategory, RHMoveEvents, RHMoveSubcategories,
                                                              RHSortSubcategories, RHSplitCategory)
from indico.modules.users import User
from indico.web.flask.util import make_compat_redirect_func, redirect_view, url_for
from indico.web.flask.wrappers import IndicoBlueprint


def _redirect_event_creation(category_id, event_type):
    anchor = 'create-event:{}:{}'.format(event_type, category_id)
    return redirect(url_for('.display', category_id=category_id, _anchor=anchor))


_bp = IndicoBlueprint('categories', __name__, template_folder='templates', virtual_template_folder='categories',
                      url_prefix='/category/<int:category_id>')

# Category management
_bp.add_url_rule('/manage/', 'manage_content', RHManageCategoryContent)
_bp.add_url_rule('/manage/delete', 'delete', RHDeleteCategory, methods=('POST',))
_bp.add_url_rule('/manage/icon', 'manage_icon', RHManageCategoryIcon, methods=('POST', 'DELETE'))
_bp.add_url_rule('/manage/logo', 'manage_logo', RHManageCategoryLogo, methods=('POST', 'DELETE'))
_bp.add_url_rule('/manage/move', 'move', RHMoveCategory, methods=('POST',))
_bp.add_url_rule('/manage/protection', 'manage_protection', RHManageCategoryProtection, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/settings', 'manage_settings', RHManageCategorySettings, methods=('POST', 'GET'))

# Event management
_bp.add_url_rule('/manage/events/delete', 'delete_events', RHDeleteEvents, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/events/move', 'move_events', RHMoveEvents, methods=('POST',))
_bp.add_url_rule('/manage/events/split', 'split_category', RHSplitCategory, methods=('GET', 'POST'))

# Subcategory management
_bp.add_url_rule('/manage/subcategories/create', 'create_subcategory', RHCreateCategory, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/subcategories/delete', 'delete_subcategories', RHDeleteSubcategories, methods=('POST',))
_bp.add_url_rule('/manage/subcategories/move', 'move_subcategories', RHMoveSubcategories, methods=('POST',))
_bp.add_url_rule('/manage/subcategories/sort', 'sort_subcategories', RHSortSubcategories, methods=('POST',))

# Display
_bp.add_url_rule('!/', 'display', RHDisplayCategory, defaults={'category_id': 0})
_bp.add_url_rule('/', 'display', RHDisplayCategory)
_bp.add_url_rule('/event-list', 'event_list', RHEventList)
_bp.add_url_rule('/events.atom', 'export_atom', RHExportCategoryAtom)
_bp.add_url_rule('/events.ics', 'export_ical', RHExportCategoryICAL)
_bp.add_url_rule('/events.rss', 'export_rss', make_compat_redirect_func(_bp, 'export_atom'))
_bp.add_url_rule('/icon-<slug>.png', 'display_icon', RHCategoryIcon)
_bp.add_url_rule('/info', 'info', RHCategoryInfo)
_bp.add_url_rule('/info-from', 'info_from', RHReachableCategoriesInfo, methods=('GET', 'POST'))
_bp.add_url_rule('/logo-<slug>.png', 'display_logo', RHCategoryLogo)
_bp.add_url_rule('/overview', 'overview', RHCategoryOverview)
_bp.add_url_rule('/show-future-events', 'show_future_events', RHShowFutureEventsInCategory, methods=('DELETE', 'PUT'))
_bp.add_url_rule('/show-past-events', 'show_past_events', RHShowPastEventsInCategory, methods=('DELETE', 'PUT'))
_bp.add_url_rule('/statistics', 'statistics', RHCategoryStatistics)
_bp.add_url_rule('/subcat-info', 'subcat_info', RHSubcatInfo)
_bp.add_url_rule('/calendar', 'calendar', RHCategoryCalendarView)

# Event creation - redirect to anchor page opening the dialog
_bp.add_url_rule('/create/event/<any(lecture,meeting,conference):event_type>', view_func=_redirect_event_creation)

# TODO: remember to refactor it at some point
_bp.add_url_rule('!/xmlGateway.py/getCategoryInfo', 'category_xml_info', RHXMLExportCategoryInfo)

# Short URLs
_bp.add_url_rule('!/categ/<int:category_id>', view_func=redirect_view('.display'), strict_slashes=False)
_bp.add_url_rule('!/c/<int:category_id>', view_func=redirect_view('.display'), strict_slashes=False)

# Internal API
_bp.add_url_rule('!/category/search', 'search', RHCategorySearch)

# Administration
_bp.add_url_rule('!/admin/upcoming-events', 'manage_upcoming', RHManageUpcomingEvents, methods=('GET', 'POST'))


@_bp.before_request
def _redirect_to_bootstrap():
    # No users in Indico yet? Redirect from index page to bootstrap form
    if (request.endpoint == 'categories.display' and not request.view_args['category_id'] and
            not User.query.filter_by(is_system=False).has_rows()):
        return redirect(url_for('bootstrap.index'))


_compat_bp = IndicoBlueprint('compat_categories', __name__)
_compat_bp.add_url_rule('/category/<legacy_category_id>/<path:path>', 'legacy_id', compat_category)
_compat_bp.add_url_rule('/category/<legacy_category_id>/', 'legacy_id', compat_category)
_compat_bp.add_url_rule('!/categoryDisplay.py', 'display_modpython',
                        make_compat_redirect_func(_compat_bp, 'legacy_id',
                                                  view_args_conv={'categId': 'legacy_category_id'}))
