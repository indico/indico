# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission, check_permissions
from indico.core.settings import SettingsProxy
from indico.modules.categories.models.categories import Category
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('categories')

upcoming_events_settings = SettingsProxy('upcoming_events', {
    'entries': [],
    'max_entries': 10
})


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.categories.tasks  # noqa: F401


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.categories.models.principals import CategoryPrincipal
    CategoryPrincipal.merge_users(target, source, 'category')


@signals.menu.items.connect_via('category-management-sidemenu')
def _sidemenu_items(sender, category, **kwargs):
    yield SideMenuItem('content', _('Content'), url_for('categories.manage_content', category),
                       100, icon='eye')
    yield SideMenuItem('settings', _('Settings'), url_for('categories.manage_settings', category),
                       90, icon='settings')
    yield SideMenuItem('protection', _('Protection'), url_for('categories.manage_protection', category),
                       70, icon='shield')
    yield SideMenuItem('roles', _('Roles'), url_for('categories.manage_roles', category),
                       50, icon='users')


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('upcoming_events', _('Upcoming events'), url_for('categories.manage_upcoming'),
                           section='homepage')


@signals.app_created.connect
def _check_permissions(app, **kwargs):
    check_permissions(Category)


@signals.acl.get_management_permissions.connect_via(Category)
def _get_management_permissions(sender, **kwargs):
    return CreatorPermission


class CreatorPermission(ManagementPermission):
    name = 'create'
    friendly_name = _('Event creation')
    description = _('Allows creating events in the category')
    user_selectable = True
