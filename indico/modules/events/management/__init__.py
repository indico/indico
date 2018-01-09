# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from indico.core.config import config
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
        if config.ENABLE_ROOMBOOKING:
            yield SideMenuItem('room_booking', _('Room Booking'),
                               url_for('event_mgmt.rooms_booking_list', event),
                               50,
                               icon='location')
        yield SideMenuItem('protection', _('Protection'), url_for('event_management.protection', event),
                           60, icon='shield')
