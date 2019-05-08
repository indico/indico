# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, SideMenuSection


@signals.menu.sections.connect_via('event-management-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield SideMenuSection('organization', _("Organization"), 50, icon='list', active=True)
    yield SideMenuSection('services', _("Services"), 40, icon='broadcast')
    yield SideMenuSection('reports', _("Reports"), 30, icon='stack')
    yield SideMenuSection('customization', _("Customization"), 20, icon='image')
    yield SideMenuSection('advanced', _("Advanced options"), 10, icon='lamp')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):
    if event.can_manage(session.user):
        yield SideMenuItem('settings', _('Settings'), url_for('event_management.settings', event), 100, icon='settings')
        yield SideMenuItem('protection', _('Protection'), url_for('event_management.protection', event),
                           60, icon='shield')
