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
from indico.core.logger import Logger
from indico.modules.events.layout.default import DEFAULT_MENU_ENTRIES
from indico.modules.events.settings import EventSettingsProxy
from indico.web.flask.util import url_for


logger = Logger.get('events.layout')
layout_settings = EventSettingsProxy('layout', {
    'is_searchable': True,
    'show_nav_bar': True,
    'show_social_badges': True,
    'show_banner': False,
    'header_text_color': None,
    'header_background_color': None,
    'announcement': None,
    'show_annoucement': False
    # TODO: handle style sheets
})


@signals.event_management.sidemenu_advanced.connect
def _extend_event_management_menu_layout(event, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'layout', SideMenuItem('Layout', url_for('event_layout.index', event),
                                  visible=event.canModify(session.user))


@signals.event_management.sidemenu_advanced.connect
def _extend_event_management_menu_event_menu(event, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'menu', SideMenuItem('Menu', url_for('event_layout.menu', event), visible=event.canModify(session.user))


@signals.event.sidemenu.connect
def _get_default_menu_entries(sender, **kwargs):
    for entry in DEFAULT_MENU_ENTRIES:
        yield entry
