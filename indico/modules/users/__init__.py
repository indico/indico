# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.notifications import make_email, send_email
from indico.core.settings import SettingsProxy
from indico.core.settings.converters import EnumConverter
from indico.modules.users.ext import ExtraUserPreferences
from indico.modules.users.models.settings import UserSetting, UserSettingsProxy
from indico.modules.users.models.users import NameFormat, User
from indico.util.i18n import _, force_locale
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, TopMenuItem


__all__ = ('ExtraUserPreferences', 'User', 'UserSetting', 'UserSettingsProxy', 'user_settings')

logger = Logger.get('users')

user_settings = UserSettingsProxy('users', {
    'lang': None,
    'force_language': False,
    'timezone': None,
    'force_timezone': False,  # always use the user's timezone instead of an event's timezone
    'show_future_events': False,
    'show_past_events': False,
    'name_format': NameFormat.first_last,
    'use_previewer_pdf': True,
    'add_ical_alerts': False,
    'add_ical_alerts_mins': 5,
    'use_markdown_for_minutes': False,
    'synced_fields': None,  # None to synchronize all fields, empty set to not synchronize
    'suggest_categories': False,  # whether the user should receive category suggestions
    'mastodon_server_url': None,
    'mastodon_server_name': None,
}, converters={
    'name_format': EnumConverter(NameFormat),
})

user_management_settings = SettingsProxy('user_management', {
    'notify_account_creation': False,
    'email_blacklist': [],
    'allow_personal_tokens': True,
    'mandatory_fields_account_request': []
})


@signals.category.deleted.connect
def _category_deleted(category, **kwargs):
    category.favorite_of.clear()


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('admins', _('Admins'), url_for('users.admins'), section='user_management')
        yield SideMenuItem('users', _('Users'), url_for('users.users_admin'), section='user_management')


@signals.menu.items.connect_via('user-profile-sidemenu')
def _sidemenu_items(sender, user, **kwargs):
    yield SideMenuItem('dashboard', _('Dashboard'), url_for('users.user_dashboard'), 100, disabled=user.is_system)
    yield SideMenuItem('personal_data', _('Personal data'), url_for('users.user_profile'), 90)
    yield SideMenuItem('profile_picture', _('Profile picture'), url_for('users.user_profile_picture_page'), 80,
                       disabled=user.is_system)
    yield SideMenuItem('emails', _('Emails'), url_for('users.user_emails'), 70, disabled=user.is_system)
    yield SideMenuItem('preferences', _('Preferences'), url_for('users.user_preferences'), 60, disabled=user.is_system)
    yield SideMenuItem('favorites', _('Favorites'), url_for('users.user_favorites'), 50, disabled=user.is_system)
    yield SideMenuItem('data_export', _('Data export'), url_for('users.user_data_export'), 0, disabled=user.is_system)


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    if session.user:
        yield TopMenuItem('profile', _('My profile'), url_for('users.user_dashboard', user_id=None), 50)


@signals.users.registration_requested.connect
def _registration_requested(req, **kwargs):
    from indico.modules.users.util import get_admin_emails
    with force_locale(None):
        tpl = get_template_module('users/emails/profile_requested_admins.txt', req=req)
        email = make_email(get_admin_emails(), template=tpl)
    send_email(email)


@signals.users.registered.connect
def _registered(user, identity, from_moderation, **kwargs):
    from indico.modules.users.util import get_admin_emails
    if (from_moderation or identity is None or identity.provider != 'indico' or
            not user_management_settings.get('notify_account_creation')):
        return
    with force_locale(None):
        tpl = get_template_module('users/emails/profile_registered_admins.txt', user=user)
        email = make_email(get_admin_emails(), template=tpl)
    send_email(email)


@signals.core.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.users.tasks  # noqa: F401
