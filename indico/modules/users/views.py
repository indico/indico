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

from flask import request

from indico.legacy.webinterface.pages.base import WPJinjaMixin
from indico.legacy.webinterface.pages.main import WPMainBase
from indico.legacy.webinterface.wcomponents import WSimpleNavigationDrawer
from indico.modules.admin.views import WPAdmin
from indico.modules.users import User
from indico.util.i18n import _


class WPUser(WPJinjaMixin, WPMainBase):
    """Base WP for user profile pages.

    Whenever you use this, you MUST include `user` in the params passed to
    `render_template`. Any RH using this should inherit from `RHUserBase`
    which already handles user/admin access. In this case, simply add
    ``user=self.user`` to your `render_template` call.
    """

    template_prefix = 'users/'

    def __init__(self, rh, active_menu_item, **kwargs):
        kwargs['active_menu_item'] = active_menu_item
        WPMainBase.__init__(self, rh, **kwargs)

    def _getNavigationDrawer(self):
        if 'user_id' in request.view_args:
            user = User.get(request.view_args['user_id'])
            profile_breadcrumb = _('Profile of {name}').format(name=user.full_name)
        else:
            profile_breadcrumb = _('My Profile')
        return WSimpleNavigationDrawer(profile_breadcrumb)

    def _getBody(self, params):
        return self._getPageContent(params)


class WPUsersAdmin(WPAdmin):
    template_prefix = 'users/'

    def getJSFiles(self):
        return WPAdmin.getJSFiles(self) + self._asset_env['modules_users_js'].urls()
