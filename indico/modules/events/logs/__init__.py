# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.modules.events.logs.models.entries import EventLogEntry, EventLogKind, EventLogRealm
from indico.modules.events.logs.renderers import EmailRenderer, SimpleRenderer
from indico.modules.events.logs.util import get_log_renderers
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('EventLogEntry', 'EventLogKind', 'EventLogRealm')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user):
        return
    return SideMenuItem('logs', _('Logs'), url_for('event_logs.index', event), section='reports')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    EventLogEntry.find(user_id=source.id).update({EventLogEntry.user_id: target.id})


@signals.event.get_log_renderers.connect
def _get_log_renderers(sender, **kwargs):
    yield SimpleRenderer
    yield EmailRenderer


@signals.app_created.connect
def _check_agreement_definitions(app, **kwargs):
    # This will raise RuntimeError if the log renderer types are not unique
    get_log_renderers()
