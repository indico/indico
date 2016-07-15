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

from markupsafe import escape

from indico.util.i18n import _
from MaKaC.webinterface.pages.admins import WPAdminsBase
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import WNavigationDrawer


class WPManageUpcomingEvents(WPJinjaMixin, WPAdminsBase):
    sidemenu_option = 'upcoming_events'
    template_prefix = 'categories/'


class WPCategory(WPJinjaMixin, WPMainBase):
    """WP for category display pages"""

    template_prefix = 'categories/'

    def __init__(self, rh, category, **kwargs):
        kwargs['category'] = category
        self.category = category
        self.atom_feed_url = kwargs.get('atom_feed_url')
        self.atom_feed_title = kwargs.get('atom_feed_title')
        if category:
            self._setTitle('Indico [{}]'.format(category.title).encode('utf-8'))
        WPMainBase.__init__(self, rh, _protected_object=category, _current_category=category, **kwargs)
        if category:
            self._locTZ = category.display_tzinfo.zone

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + self._asset_env['category_sass'].urls()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._asset_env['modules_categories_js'].urls()

    def _getBody(self, params):
        return self._getPageContent(params)

    def _getHeadContent(self):
        head_content = WPMainBase._getHeadContent(self)
        if self.atom_feed_url:
            title = self.atom_feed_title or _("Indico Atom feed")
            head_content += ('<link rel="alternate" type="application/atom+xml" title="{}" href="{}">'
                             .format(escape(title), self.atom_feed_url))
        return head_content

    def _getNavigationDrawer(self):
        if self.category and not self.category.is_root:
            return WNavigationDrawer({'target': self.category})


class WPCategoryManagement(WPCategory):
    """WP for category management pages"""

    MANAGEMENT = True

    def __init__(self, rh, category, active_menu_item, **kwargs):
        kwargs['active_menu_item'] = active_menu_item
        WPCategory.__init__(self, rh, category, **kwargs)
        # don't show protection header in management; anything besides 'restricted' would be misleading
        self._protected_object = None

    def getCSSFiles(self):
        return WPCategory.getCSSFiles(self) + self._asset_env['category_management_sass'].urls()

    def getJSFiles(self):
        return WPCategory.getJSFiles(self) + self._asset_env['modules_categories_management_js'].urls()

    def _getNavigationDrawer(self):
        if not self.category.is_root:
            return WNavigationDrawer({'target': self.category, 'isModif': True}, bgColor="white")


class WPCategoryStatistics(WPCategory):
    def getJSFiles(self):
        return (WPCategory.getJSFiles(self) +
                self._includeJSPackage('jqplot_js', prefix='') +
                self._asset_env['statistics_js'].urls() +
                self._asset_env['modules_category_statistics_js'].urls())

    def getCSSFiles(self):
        return WPCategory.getCSSFiles(self) + self._asset_env['jqplot_css'].urls()
