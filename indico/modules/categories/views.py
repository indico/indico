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

from flask import render_template

from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.category import WPCategoryDisplayBase
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import WSimpleNavigationDrawer
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import MenuItem, render_sidemenu


class WPCategoryManagement(WPJinjaMixin, WPMainBase):
    """WP for catagory management pages

    The category must be passed as 'category' parameter when rendering.
    """

    template_prefix = 'categories/'

    def _getBody(self, params):
        category = params['category']
        params['side_menu'] = render_sidemenu('category-management-sidemenu', old_style=True, category=category,
                                              active_item=params.get('active_menu_item'))
        return self._getPageContent(params)


class WPCategoryStatistics(WPJinjaMixin, WPCategoryDisplayBase):
    template_prefix = 'categories/'

    def _getBody(self, params):
        return self._getPageContent(params)

    def _getNavigationDrawer(self):
        return WSimpleNavigationDrawer(self._target.getName(), type='Statistics')

    def getJSFiles(self):
        return (WPCategoryDisplayBase.getJSFiles(self) + self._includeJSPackage('jqplot_js', prefix='')
                + self._asset_env['statistics_js'].urls() + self._asset_env['modules_category_statistics_js'].urls())

    def getCSSFiles(self):
        return WPCategoryDisplayBase.getCSSFiles(self) + self._asset_env['jqplot_css'].urls()
