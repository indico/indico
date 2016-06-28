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

from indico.modules.categories.controllers.display import (RHCategoryStatistics, RHCategoryIcon, RHCategoryLogo,
                                                           RHCategoryInfo, RHCategorySearch)
from indico.modules.categories.controllers.management import (RHCreateCategory, RHDeleteCategory, RHDeleteEvents,
                                                              RHDeleteSubcategories, RHManageCategoryContent,
                                                              RHManageCategoryIcon, RHManageCategoryLogo,
                                                              RHManageCategoryProtection, RHManageCategorySettings,
                                                              RHMoveCategory, RHMoveEvents, RHMoveSubcategories,
                                                              RHSortSubcategories, RHSplitCategory)
from indico.web.flask.wrappers import IndicoBlueprint


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
_bp.add_url_rule('/icon-<slug>.png', 'display_icon', RHCategoryIcon)
_bp.add_url_rule('/logo-<slug>.png', 'display_logo', RHCategoryLogo)
_bp.add_url_rule('/statistics', 'statistics', RHCategoryStatistics)
_bp.add_url_rule('/info', 'info', RHCategoryInfo)

# Internal API
_bp.add_url_rule('!/category/search', 'search', RHCategorySearch)
