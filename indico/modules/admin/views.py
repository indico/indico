# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.legacy.webinterface.pages.base import WPJinjaMixin
from indico.legacy.webinterface.pages.main import WPMainBase
from indico.legacy.webinterface.wcomponents import WSimpleNavigationDrawer
from indico.util.i18n import _
from indico.web.menu import get_menu_item


class WPAdmin(WPJinjaMixin, WPMainBase):
    """Base class for admin pages."""

    def __init__(self, rh, active_menu_item=None, **kwargs):
        kwargs['active_menu_item'] = active_menu_item or self.sidemenu_option
        WPMainBase.__init__(self, rh, **kwargs)

    def _getNavigationDrawer(self):
        menu_item = get_menu_item('admin-sidemenu', self._kwargs['active_menu_item'])
        items = [_('Administration')]
        if menu_item:
            items.append(menu_item.title)
        return WSimpleNavigationDrawer(*items)

    def _getBody(self, params):
        return self._getPageContent(params)
