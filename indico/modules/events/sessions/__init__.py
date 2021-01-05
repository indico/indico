# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission, check_permissions
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import has_sessions_for_user
from indico.modules.events.settings import EventSettingsProxy
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.sessions')
session_settings = EventSettingsProxy('sessions', {
    # Whether session coordinators can manage contributions inside their sessions
    'coordinators_manage_contributions': False,
    # Whether session coordinators can manage their session blocks
    'coordinators_manage_blocks': False
})


COORDINATOR_PRIV_SETTINGS = {'manage-contributions': 'coordinators_manage_contributions',
                             'manage-blocks': 'coordinators_manage_blocks'}
COORDINATOR_PRIV_TITLES = {'manage-contributions': _('Contributions'),
                           'manage-blocks': _('Session blocks')}
COORDINATOR_PRIV_DESCS = {'manage-contributions': _('Allows coordinators to modify contributions in their sessions.'),
                          'manage-blocks': _('Allows coordinators to manage/reschedule session blocks of their '
                                             'sessions.  This includes creating new session blocks.')}


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


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user):
        return
    if event.type == 'conference':
        return SideMenuItem('sessions', _('Sessions'), url_for('sessions.session_list', event), section='organization')


@signals.event_management.get_cloners.connect
def _get_session_cloner(sender, **kwargs):
    from indico.modules.events.sessions.clone import SessionCloner
    return SessionCloner


@signals.app_created.connect
def _check_permissions(app, **kwargs):
    check_permissions(Session)


@signals.acl.get_management_permissions.connect_via(Session)
def _get_management_permissions(sender, **kwargs):
    return CoordinatorPermission


class CoordinatorPermission(ManagementPermission):
    name = 'coordinate'
    friendly_name = _('Coordination')
    description = _('Grants coordination access to the session.')
    user_selectable = True


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.layout.util import MenuEntryData

    def _visible_my_sessions(event):
        return session.user and has_sessions_for_user(event, session.user)

    yield MenuEntryData(title=_("My Sessions"), name='my_sessions', endpoint='sessions.my_sessions', position=1,
                        parent='my_conference', visible=_visible_my_sessions)
