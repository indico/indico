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

from flask import session

from indico.core import signals
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind, EventLogEntry
from indico.modules.events.logs.renderers import SimpleRenderer, EmailRenderer
from indico.modules.events.logs.util import get_log_renderers
from indico.web.flask.util import url_for

__all__ = ['EventLogEntry', 'EventLogKind']


@signals.event_management.sidemenu_advanced.connect
def _extend_event_management_menu(event, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    if not event.as_event.can_manage(session.user, allow_key=True):
        return
    return 'logs', SideMenuItem('Logs', url_for('event_logs.index', event), section='advanced')


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
