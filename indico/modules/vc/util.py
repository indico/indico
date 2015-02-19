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
from indico.modules.vc import VCPluginMixin
from indico.modules.vc.models.vc_rooms import VCRoomLinkType


def get_vc_plugins():
    """Returns a dict containing the available video conference plugins."""
    return {p.service_name: p for p in plugin_engine.get_active_plugins().itervalues()
            if isinstance(p, VCPluginMixin)}


def get_vc_plugin_by_service_name(plugin_name):
    """Returns a video conference plugin"""
    for name, plugin in get_vc_plugins().iteritems():
        if name == plugin_name:
            return plugin
    else:
        raise KeyError()


def process_form_data(data):
    name = data.pop('name')
    contribution_id = data.pop('contribution')
    session_id = data.pop('session')
    link_type = VCRoomLinkType[data.pop('linking')]
    if link_type == VCRoomLinkType.event:
        link_id = None
    else:
        link_id = int(contribution_id if link_type == VCRoomLinkType.contribution else session_id)

    return data, name, link_type, link_id


def update_vc_room(vc_room, name, data):
    vc_room.name = name
    if vc_room.data is None:
        vc_room.data = {}
    vc_room.data.update(data)
