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

from flask import render_template, session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.notifications import make_email, send_email
from indico.core.settings import SettingsProxy
from indico.core.settings.converters import EnumConverter
from indico.modules.users.ext import ExtraUserPreferences
from indico.modules.users.models.settings import UserSetting, UserSettingsProxy
from indico.modules.users.models.users import NameFormat, User
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module, template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem


__all__ = ('ExtraUserPreferences', 'User', 'UserSetting', 'UserSettingsProxy', 'user_settings')

logger = Logger.get('users')

user_settings = UserSettingsProxy('users', {
    'lang': None,
    'timezone': None,
    'force_timezone': False,  # always use the user's timezone instead of an event's timezone
    'show_past_events': False,
    'name_format': NameFormat.first_last,
    'use_previewer_pdf': True,
    'synced_fields': None,  # None to synchronize all fields, empty set to not synchronize
    'suggest_categories': False  # whether the user should receive category suggestions
}, converters={
    'name_format': EnumConverter(NameFormat)
})

user_management_settings = SettingsProxy('user_management', {
    'notify_account_creation': False
})


@signals.category.deleted.connect
def _category_deleted(category, **kwargs):
    category.favorite_of.clear()


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('admins', _("Admins"), url_for('users.admins'), section='user_management')
        yield SideMenuItem('users', _("Users"), url_for('users.users_admin'), section='user_management')


@signals.menu.items.connect_via('user-profile-sidemenu')
def _sidemenu_items(sender, user, **kwargs):
    yield SideMenuItem('dashboard', _('Dashboard'), url_for('users.user_dashboard'), 100, disabled=user.is_system)
    yield SideMenuItem('personal_data', _('Personal data'), url_for('users.user_profile'), 90)
    yield SideMenuItem('emails', _('Emails'), url_for('users.user_emails'), 80, disabled=user.is_system)
    yield SideMenuItem('preferences', _('Preferences'), url_for('users.user_preferences'), 70, disabled=user.is_system)
    yield SideMenuItem('favorites', _('Favourites'), url_for('users.user_favorites'), 60, disabled=user.is_system)


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    if session.user:
        yield TopMenuItem('profile', _('My profile'), url_for('users.user_dashboard', user_id=None), 50)


@template_hook('global-announcement', priority=-1)
def _inject_login_as_header(**kwargs):
    login_as_data = session.get('login_as_orig_user')
    if login_as_data:
        return render_template('users/login_as_header.html', login_as_data=login_as_data)


@signals.users.registration_requested.connect
def _registration_requested(req, **kwargs):
    from indico.modules.users.util import get_admin_emails
    tpl = get_template_module('users/emails/profile_requested_admins.txt', req=req)
    send_email(make_email(get_admin_emails(), template=tpl))


@signals.users.registered.connect
def _registered(user, identity, from_moderation, **kwargs):
    from indico.modules.users.util import get_admin_emails
    if (from_moderation or identity is None or identity.provider != 'indico' or
            not user_management_settings.get('notify_account_creation')):
        return
    tpl = get_template_module('users/emails/profile_registered_admins.txt', user=user)
    send_email(make_email(get_admin_emails(), template=tpl))
