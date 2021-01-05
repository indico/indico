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
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.roles')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if event.can_manage(session.user):
        roles_section = 'organization' if event.type == 'conference' else 'advanced'
        return SideMenuItem('roles', _('Roles Setup'), url_for('event_roles.manage', event), section=roles_section)


@signals.event_management.get_cloners.connect
def _get_event_roles_cloner(sender, **kwargs):
    from indico.modules.events.roles.clone import EventRoleCloner
    return EventRoleCloner
