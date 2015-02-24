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

from flask import render_template

from indico.core import signals
from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation
from indico.modules.vc.plugins import VCPluginMixin
from indico.modules.vc.forms import VCPluginSettingsFormBase
from indico.web.flask.templating import template_hook, get_overridable_template_name
from MaKaC.webinterface.displayMgr import EventMenuEntry

__all__ = ('VCPluginMixin', 'VCPluginSettingsFormBase')


@template_hook('event-header')
def _inject_event_header(event, **kwargs):
    """Fetches the VC rooms attached only to the whole event and display them in the event page
    header"""
    event_vc_rooms = VCRoomEventAssociation.find_for_event_linked_to_event(event).all()
    return render_template('vc/event_header.html', event=event, event_vc_rooms=event_vc_rooms)


@template_hook('vc-actions')
def _inject_vc_room_action_buttons(event, item, event_vc_rooms_dict, **kwargs):
    event_vc_room = event_vc_rooms_dict.get(item)
    if event_vc_room:
        tpl = get_overridable_template_name('vc_room_timetable_buttons.html', event_vc_room.vc_room.plugin, 'vc/')
        return render_template(tpl, event=event, event_vc_room=event_vc_room, **kwargs)
    return


def extend_event_menu(sender, **kwargs):
    return EventMenuEntry('vc.event_videoconference', 'Video Conference Rooms', name='vc-event-page')

signal = signals.event.sidemenu
signal.connect(extend_event_menu, **{'weak': False})
