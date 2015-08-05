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

from indico.core.plugins import plugin_engine
from indico.modules.events.models.events import Event
from indico.util.i18n import _

from MaKaC.conference import SessionSlot


def get_vc_plugins():
    """Returns a dict containing the available videoconference plugins."""
    from indico.modules.vc import VCPluginMixin

    return {p.service_name: p for p in plugin_engine.get_active_plugins().itervalues()
            if isinstance(p, VCPluginMixin)}


def full_block_id(block):
    return "{}:{}".format(block.session.id, block.id)


def resolve_title(obj):
    if isinstance(obj, SessionSlot):
        return obj.getFullTitle().decode('utf-8')
    else:
        return obj.getTitle().decode('utf-8')


def get_linked_to_description(obj):
    return {
        'event': _('{} (event)'),
        'contribution': _('{} (contribution)'),
        'block': _('{} (session block)'),
    }[obj.link_type.name].format(resolve_title(obj.link_object))


def get_managed_vc_plugins(user):
    """Returns the plugins the user can manage"""
    return [p for p in get_vc_plugins().itervalues() if p.can_manage_vc(user)]


def find_event_vc_rooms(from_dt=None, to_dt=None, distinct=False):
    """Finds VC rooms matching certain criteria

    :param from_dt: earliest event/contribution to include
    :param to_dt: latest event/contribution to include
    :param distinct: if True, never return the same ``(event, vcroom)``
                     more than once (even if it's linked more than once to
                     that event)
    """
    from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation
    query = VCRoomEventAssociation.find()
    if distinct:
        query = query.distinct(VCRoomEventAssociation.event_id, VCRoomEventAssociation.vc_room_id)
    if from_dt is not None or to_dt is not None:
        query = query.join(Event, Event.id == VCRoomEventAssociation.event_id)
        if from_dt is not None:
            query = query.filter(Event.start_date >= from_dt)
        if to_dt is not None:
            query = query.filter(Event.start_date < to_dt)
    for vc_room in query:
        yield vc_room
