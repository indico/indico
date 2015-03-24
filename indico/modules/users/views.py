# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from operator import attrgetter

from indico.core import signals
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.web.menu import MenuItem

from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import WSimpleNavigationDrawer


class WPUser(WPJinjaMixin, WPMainBase):
    """Base WP for user profile pages.

    Whenever you use this, you MUST include `user` in the params passed to
    `render_template`. Any RH using this should inherit from `RHUserBase`
    which already handles user/admin access. In this case, simply add
    ``user=self.user`` to your `render_template` call.
    """

    template_prefix = 'users/'

    def _getNavigationDrawer(self):
        return WSimpleNavigationDrawer(_('My Profile'))

    def _getBody(self, params):
        extra_items = sorted(values_from_signal(signals.users.profile_sidemenu.send(params['user'])),
                             key=attrgetter('title'))
        params['user_menu_items'] = [
            MenuItem(_('Dashboard'), 'users.user_dashboard'),
            MenuItem(_('Account details'), 'users.user_account'),
            MenuItem(_('Preferences'), 'users.user_preferences'),
            MenuItem(_('Favorites'), 'users.user_favorites'),
            # TODO: other menu items
        ] + extra_items
        return self._getPageContent(params)


class WPUserDashboard(WPUser):
    def getCSSFiles(self):
        return WPUser.getCSSFiles(self) + self._asset_env['dashboard_sass'].urls()
