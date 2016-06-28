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

from flask import session, render_template

from indico.core import signals
from indico.core.logger import Logger
from indico.core.settings.core import SettingsProxy
from indico.modules.users.ext import ExtraUserPreferences
from indico.modules.users.models.users import User
from indico.modules.users.models.settings import UserSetting, UserSettingsProxy
from indico.util.i18n import _
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('ExtraUserPreferences', 'User', 'UserSetting', 'UserSettingsProxy', 'user_settings')

logger = Logger.get('users')

user_settings = UserSettingsProxy('users', {
    'lang': None,
    'timezone': None,
    'force_timezone': False,  # always use the user's timezone instead of an event's timezone
    'show_past_events': False,
    'use_previewer_pdf': True,
    'synced_fields': None  # None to synchronise all fields, empty set to not synchronize
})

user_management_settings = SettingsProxy('user_management', {
    'notify_account_creation': False
})


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    return SideMenuItem('users', _("Users"), url_for('users.users_admin'), section='user_management')


@signals.category.deleted.connect
def _category_deleted(category, **kwargs):
    category.favorite_of.clear()


@signals.menu.items.connect_via('user-profile-sidemenu')
def _sidemenu_items(sender, **kwargs):
    yield SideMenuItem('dashboard', _('Dashboard'), url_for('users.user_dashboard'), 100)
    yield SideMenuItem('personal_data', _('Personal data'), url_for('users.user_profile'), 90)
    yield SideMenuItem('emails', _('Emails'), url_for('users.user_emails'), 80)
    yield SideMenuItem('preferences', _('Preferences'), url_for('users.user_preferences'), 70)
    yield SideMenuItem('favorites', _('Favourites'), url_for('users.user_favorites'), 60)


@template_hook('global-announcement', priority=-1)
def _inject_login_as_header(**kwargs):
    login_as_data = session.get('login_as_orig_user')
    if login_as_data:
        return render_template('users/login_as_header.html', login_as_data=login_as_data)
