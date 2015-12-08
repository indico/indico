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

from flask import flash, session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.roles import ManagementRole, check_roles
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import can_manage_sessions
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.sessions')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.sessions.models.principals import SessionPrincipal
    SessionPrincipal.merge_users(target, source, 'session')


@signals.users.registered.connect
@signals.users.email_added.connect
def _convert_email_principals(user, **kwargs):
    from indico.modules.events.sessions.models.principals import SessionPrincipal
    sessions = SessionPrincipal.replace_email_with_user(user, 'session')
    if sessions:
        num = len(sessions)
        flash(ngettext("You have been granted manager/coordination privileges for a session.",
                       "You have been granted manager/coordination privileges for {} sessions.", num).format(num),
              'info')


@signals.app_created.connect
def _check_roles(app, **kawrgs):
    check_roles(Session)


@signals.acl.get_management_roles.connect_via(Session)
def _get_management_roles(sender, **kwargs):
    return CoordinatorRole


class CoordinatorRole(ManagementRole):
    name = 'coordinate'
    friendly_name = _('Coordination')
    description = _('Grants coordination access to the session.')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not can_manage_sessions(session.user, event, 'ANY'):
        return
    return SideMenuItem('sessions', _('Sessions'), url_for('sessions.session_list', event), section='organization')


@signals.event_management.management_url.connect
def _get_event_management_url(event, **kwargs):
    if can_manage_sessions(session.user, event.as_event, 'ANY'):
        return url_for('sessions.session_list', event)
