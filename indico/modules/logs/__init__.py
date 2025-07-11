# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.modules.logs.models.entries import (AppLogEntry, AppLogRealm, CategoryLogEntry, CategoryLogRealm,
                                                EventLogEntry, EventLogRealm, LogKind)
from indico.modules.logs.renderers import EmailRenderer, SimpleRenderer
from indico.modules.logs.util import get_log_renderers
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('AppLogEntry', 'CategoryLogEntry', 'EventLogEntry', 'EventLogRealm', 'AppLogRealm', 'CategoryLogRealm',
           'LogKind')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if event.can_manage(session.user):
        return SideMenuItem('logs', _('Logs'), url_for('logs.event', event), section='reports')


@signals.menu.items.connect_via('user-profile-sidemenu')
def _extend_user_profile_sidemenu(sender, user, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('logs', _('Logs'), url_for('logs.user'), -100)


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    EventLogEntry.query.filter_by(user_id=source.id).update({EventLogEntry.user_id: target.id})
    CategoryLogEntry.query.filter_by(user_id=source.id).update({CategoryLogEntry.user_id: target.id})


@signals.event.get_log_renderers.connect
def _get_log_renderers(sender, **kwargs):
    yield SimpleRenderer
    yield EmailRenderer


@signals.core.app_created.connect
def _check_log_renderers(app, **kwargs):
    # This will raise RuntimeError if the log renderer types are not unique
    get_log_renderers()


@signals.menu.items.connect_via('admin-sidemenu')
def _extend_admin_menu(sender, **kwargs):
    if session.user.is_admin:
        return SideMenuItem('logs', _('Logs'), url_for('logs.app'), -100, icon='stack')
