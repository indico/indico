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
from flask_pluginengine import render_plugin_template

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation, VCRoomLinkType, VCRoom
from indico.modules.vc.forms import VCPluginSettingsFormBase
from indico.modules.vc.plugins import VCPluginMixin
from indico.modules.vc.util import get_vc_plugins, get_managed_vc_plugins
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import HeaderMenuEntry
from indico.util.i18n import _
from indico.util.user import retrieve_principal
from MaKaC.conference import EventCloner
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.displayMgr import EventMenuEntry

__all__ = ('VCPluginMixin', 'VCPluginSettingsFormBase')


@template_hook('event-header')
def _inject_event_header(event, **kwargs):
    res = VCRoomEventAssociation.find_for_event(event, only_linked_to_event=True)
    event_vc_rooms = [event_vc_room for event_vc_room in res.all() if event_vc_room.vc_room.plugin is not None]
    if event_vc_rooms:
        return render_template('vc/event_header.html', event=event, event_vc_rooms=event_vc_rooms)
    return


@template_hook('vc-actions')
def _inject_vc_room_action_buttons(event, item, event_vc_rooms_dict, **kwargs):
    event_vc_room = event_vc_rooms_dict.get(item)
    if event_vc_room and event_vc_room.vc_room.plugin:
        plugin = event_vc_room.vc_room.plugin
        info_box = render_plugin_template('{}:info_box.html'.format(plugin.name), plugin=plugin,
                                          event_vc_room=event_vc_room, event=event, vc_room=event_vc_room.vc_room,
                                          retrieve_principal=retrieve_principal, settings=plugin.settings,
                                          for_tooltip=True, **kwargs)
        return render_plugin_template('{}:vc_room_timetable_buttons.html'.format(plugin.name),
                                      event=event, event_vc_room=event_vc_room, info_box=info_box, **kwargs)


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    def _visible(event):
        return (bool(get_vc_plugins()) and
                bool(VCRoomEventAssociation.find_for_event(event, only_linked_to_event=True).count()))
    return EventMenuEntry('vc.event_videoconference', 'Video Conference Rooms', name='vc-event-page', visible=_visible)


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
    for event_vc_room in VCRoomEventAssociation.find_for_event(event, include_hidden=True, include_deleted=True):
        event_vc_room.delete(_get_user())


@signals.indico_menu.connect
def extend_header_menu(sender, **kwargs):
    if not session.user or not get_managed_vc_plugins(session.user):
        return
    return HeaderMenuEntry(url_for('vc.vc_room_list'), _('Videoconference'), _('Services'))


def _get_user():
    if has_request_context() and session.user:
        return session.user
    else:
        return AvatarHolder().getById(Config.getInstance().getJanitorUserId())


class VCCloner(EventCloner):
    def get_options(self):
        enabled = bool(VCRoomEventAssociation.find_for_event(self.event, include_hidden=True).count())
        return {'vc_rooms': (_('Video conference rooms'), enabled)}

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


@signals.merge_users.connect
def _merge_users(user, merged, **kwargs):
    new_id = int(user.id)
    old_id = int(merged.id)
    VCRoom.find(created_by_id=old_id).update({'created_by_id': new_id})
