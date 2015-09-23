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

from flask import render_template, has_request_context, session

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.layout.util import MenuEntryData
from indico.modules.users import User
from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation, VCRoomLinkType, VCRoom
from indico.modules.vc.forms import VCPluginSettingsFormBase
from indico.modules.vc.plugins import VCPluginMixin
from indico.modules.vc.util import get_vc_plugins, get_managed_vc_plugins
from indico.web.flask.templating import get_overridable_template_name, template_hook
from indico.web.flask.util import url_for
from indico.web.menu import HeaderMenuEntry
from indico.util.i18n import _
from MaKaC.conference import EventCloner
from MaKaC.webinterface.wcomponents import SideMenuItem

__all__ = ('VCPluginMixin', 'VCPluginSettingsFormBase')


@template_hook('event-header')
def _inject_event_header(event, **kwargs):
    res = VCRoomEventAssociation.find_for_event(event, only_linked_to_event=True)
    event_vc_rooms = [event_vc_room for event_vc_room in res.all() if event_vc_room.vc_room.plugin is not None]
    if event_vc_rooms:
        return render_template('vc/event_header.html', event=event, event_vc_rooms=event_vc_rooms)


@template_hook('vc-actions')
def _inject_vc_room_action_buttons(event, item, **kwargs):
    event_vc_room = VCRoomEventAssociation.get_linked_for_event(event).get(item)
    if event_vc_room and event_vc_room.vc_room.plugin:
        plugin = event_vc_room.vc_room.plugin
        name = get_overridable_template_name('vc_room_timetable_buttons.html', plugin, core_prefix='vc/')
        return render_template(name, event=event, event_vc_room=event_vc_room, **kwargs)


@signals.event_management.sidemenu.connect
def _extend_event_management_menu(event, **kwargs):
    if not get_vc_plugins():
        return
    if not event.as_event.can_manage(session.user, allow_key=True):
        return
    return 'vc', SideMenuItem(_('Videoconference'), url_for('vc.manage_vc_rooms', event), section='organization')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    def _visible(event):
        return bool(get_vc_plugins()) and bool(VCRoomEventAssociation.find_for_event(event).count())
    return MenuEntryData(_('Videoconference Rooms'), 'videoconference_rooms', 'vc.event_videoconference',
                         position=14, visible=_visible)


@signals.event.session_slot_deleted.connect
def _session_slot_deleted(session_slot, **kwargs):
    event = session_slot.getConference()
    for event_vc_room in VCRoomEventAssociation.find_for_event(event, include_hidden=True, include_deleted=True):
        if event_vc_room.link_object is None:
            event_vc_room.link_type = VCRoomLinkType.event
            event_vc_room.link_id = None


@signals.event.contribution_deleted.connect
def _contrib_deleted(contrib, **kwargs):
    event = contrib.getConference()
    for event_vc_room in VCRoomEventAssociation.find_for_event(event, include_hidden=True, include_deleted=True):
        if event_vc_room.link_object is None:
            event_vc_room.link_type = VCRoomLinkType.event
            event_vc_room.link_id = None


@signals.event.deleted.connect
def _event_deleted(event, **kwargs):
    user = session.user if has_request_context() and session.user else User.get(Config.getInstance().getJanitorUserId())
    for event_vc_room in VCRoomEventAssociation.find_for_event(event, include_hidden=True, include_deleted=True):
        event_vc_room.delete(user)


@signals.indico_menu.connect
def extend_header_menu(sender, **kwargs):
    if not session.user or not get_managed_vc_plugins(session.user):
        return
    return HeaderMenuEntry(url_for('vc.vc_room_list'), _('Videoconference'), _('Services'))


class VCCloner(EventCloner):
    def get_options(self):
        enabled = bool(VCRoomEventAssociation.find_for_event(self.event, include_hidden=True).count())
        return {'vc_rooms': (_('Videoconference rooms'), enabled, True)}

    def clone(self, new_event, options):
        if 'vc_rooms' not in options:
            return
        for old_event_vc_room in VCRoomEventAssociation.find_for_event(self.event, include_hidden=True):
            event_vc_room = VCRoomEventAssociation(event_id=int(new_event.id),
                                                   link_type=old_event_vc_room.link_type,
                                                   link_id=old_event_vc_room.link_id,
                                                   show=old_event_vc_room.show,
                                                   data=old_event_vc_room.data)
            if event_vc_room.link_object is not None:
                event_vc_room.vc_room = old_event_vc_room.vc_room
                db.session.add(event_vc_room)


@signals.event_management.clone.connect
def _get_vc_cloner(event, **kwargs):
    return VCCloner(event)


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    VCRoom.find(created_by_id=source.id).update({VCRoom.created_by_id: target.id})
