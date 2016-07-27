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

from indico.util.i18n import _
from MaKaC.webinterface.pages.admins import WPAdminsBase
from MaKaC.webinterface.pages.base import WPJinjaMixin, WPDecorated


class WPNews(WPJinjaMixin, WPDecorated):
    template_prefix = 'news/'

    def _getBody(self, params):
        return self._getPageContent(params)

    def getCSSFiles(self):
        return WPDecorated.getCSSFiles(self) + self._asset_env['news_sass'].urls()

    def _getTitle(self):
        return WPDecorated._getTitle(self) + ' - ' + _("News")


class WPManageNews(WPJinjaMixin, WPAdminsBase):
    sidemenu_option = 'news'
    template_prefix = 'news/'
