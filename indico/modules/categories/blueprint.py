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

from indico.modules.categories.controllers.display import RHCategoryStatistics, RHSettingsIconDisplay
from indico.modules.categories.controllers.management import (RHManageCategoryContent, RHManageCategorySettings,
                                                              RHSettingsIconUpload, RHSettingsIconDelete)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('categories', __name__, template_folder='templates', virtual_template_folder='categories',
                      url_prefix='/category/<int:category_id>')

# Management
_bp.add_url_rule('/manage/', 'manage_content', RHManageCategoryContent)
_bp.add_url_rule('/manage/settings/', 'manage_settings', RHManageCategorySettings, methods=('POST', 'GET'))
_bp.add_url_rule('/manage/settings/upload_icon', 'upload_icon', RHSettingsIconUpload, methods=('POST',))
_bp.add_url_rule('/manage/settings/delete_icon', 'delete_icon', RHSettingsIconDelete, methods=('DELETE',))

# Display
_bp.add_url_rule('/icon', 'display_icon', RHSettingsIconDisplay)
_bp.add_url_rule('/statistics', 'statistics', RHCategoryStatistics)
