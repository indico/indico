# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db.sqlalchemy.protection import make_acl_log_fn
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission, check_permissions
from indico.core.settings import SettingsProxy
from indico.modules.categories.models.categories import Category, EventCreationMode
from indico.modules.categories.models.event_move_request import MoveRequestState
from indico.modules.logs.models.entries import CategoryLogRealm
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('categories')

upcoming_events_settings = SettingsProxy('upcoming_events', {
    'entries': [],
    'max_entries': 10
})

# Log ACL changes
signals.acl.entry_changed.connect(make_acl_log_fn(Category, CategoryLogRealm.category), sender=Category, weak=False)


@signals.core.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.categories.tasks  # noqa: F401


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.categories.models.principals import CategoryPrincipal
    CategoryPrincipal.merge_users(target, source, 'category')


def _is_moderation_visible(category):
    return (
        category.event_creation_mode == EventCreationMode.moderated or
        category.event_move_requests.filter_by(state=MoveRequestState.pending).has_rows() or
        any('event_move_request' in entry.permissions for entry in category.acl_entries)
    )


@signals.menu.items.connect_via('category-management-sidemenu')
def _sidemenu_items(sender, category, **kwargs):
    yield SideMenuItem('content', _('Content'), url_for('categories.manage_content', category),
                       100, icon='eye')
    yield SideMenuItem('settings', _('Settings'), url_for('categories.manage_settings', category),
                       90, icon='settings')
    yield SideMenuItem('protection', _('Protection'), url_for('categories.manage_protection', category),
                       70, icon='shield')
    if _is_moderation_visible(category):
        count = category.event_move_requests.filter_by(state=MoveRequestState.pending).count() or None
        yield SideMenuItem('moderation', _('Moderation'), url_for('categories.manage_moderation', category),
                           60, icon='user-reading', badge=count)
    yield SideMenuItem('roles', _('Roles'), url_for('categories.manage_roles', category),
                       50, icon='users')
    yield SideMenuItem('logs', _('Logs'), url_for('logs.category', category),
                       0, icon='stack')


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('upcoming_events', _('Upcoming events'), url_for('categories.manage_upcoming'),
                           section='homepage')


@signals.core.app_created.connect
def _check_permissions(app, **kwargs):
    check_permissions(Category)


@signals.acl.get_management_permissions.connect_via(Category)
def _get_management_permissions(sender, **kwargs):
    yield CreatorPermission
    yield EventMoveRequestPermission


class CreatorPermission(ManagementPermission):
    name = 'create'
    friendly_name = _('Event creation')
    description = _('Allows creating events in the category')
    user_selectable = True


class EventMoveRequestPermission(ManagementPermission):
    name = 'event_move_request'
    friendly_name = _('Request event move')
    description = _('Allows requesting for an event to be moved to this category')
    user_selectable = True
