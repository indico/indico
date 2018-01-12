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

from markupsafe import escape

from indico.legacy.webinterface.wcomponents import render_header
from indico.modules.admin.views import WPAdmin
from indico.util.i18n import _
from indico.util.mathjax import MathjaxMixin
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPManageUpcomingEvents(WPAdmin):
    template_prefix = 'categories/'


class WPCategory(MathjaxMixin, WPJinjaMixin, WPDecorated):
    """WP for category display pages"""

    template_prefix = 'categories/'
    ALLOW_JSON = False

    def __init__(self, rh, category, **kwargs):
        kwargs['category'] = category
        self.category = category
        self.atom_feed_url = kwargs.get('atom_feed_url')
        self.atom_feed_title = kwargs.get('atom_feed_title')
        if category:
            self.title = category.title
        WPDecorated.__init__(self, rh, **kwargs)
        self._mathjax = kwargs.pop('mathjax', False)

    def getJSFiles(self):
        return WPDecorated.getJSFiles(self) + self._asset_env['modules_categories_js'].urls()

    def _getHeader(self):
        return render_header(category=self.category, protected_object=self.category,
                             local_tz=self.category.display_tzinfo.zone)

    def _getBody(self, params):
        return self._getPageContent(params)

    def _getHeadContent(self):
        head_content = WPDecorated._getHeadContent(self)
        if self.atom_feed_url:
            title = self.atom_feed_title or _("Indico Atom feed")
            head_content += ('<link rel="alternate" type="application/atom+xml" title="{}" href="{}">'
                             .format(escape(title), self.atom_feed_url))
        if self._mathjax:
            head_content += MathjaxMixin._getHeadContent(self)
        return head_content

    def _get_breadcrumbs(self):
        if not self.category or self.category.is_root:
            return ''
        return render_breadcrumbs(category=self.category)


class WPCategoryManagement(WPCategory):
    """WP for category management pages"""

    MANAGEMENT = True

    def __init__(self, rh, category, active_menu_item, **kwargs):
        kwargs['active_menu_item'] = active_menu_item
        WPCategory.__init__(self, rh, category, **kwargs)

    def _getHeader(self):
        return render_header(category=self.category, protected_object=self.category,
                             local_tz=self.category.timezone, force_local_tz=True)

    def getJSFiles(self):
        return WPCategory.getJSFiles(self) + self._asset_env['modules_categories_management_js'].urls()

    def _get_breadcrumbs(self):
        if self.category.is_root:
            return ''
        return render_breadcrumbs(category=self.category, management=True)


class WPCategoryStatistics(WPCategory):
    def getJSFiles(self):
        return (WPCategory.getJSFiles(self) +
                self._includeJSPackage('jqplot_js', prefix='') +
                self._asset_env['statistics_js'].urls() +
                self._asset_env['modules_category_statistics_js'].urls())

    def getCSSFiles(self):
        return WPCategory.getCSSFiles(self) + self._asset_env['jqplot_css'].urls()
