# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db
from indico.modules.events.cloning import EventCloner
from indico.modules.vc import VCRoomEventAssociation, get_vc_plugins
from indico.util.i18n import _


class VCCloner(EventCloner):
    name = 'vc'
    friendly_name = _('Videoconference rooms')
    uses = {'sessions', 'contributions'}

    @property
    def is_visible(self):
        return bool(get_vc_plugins())

    @property
    def is_available(self):
        return bool(VCRoomEventAssociation.find_for_event(self.old_event, include_hidden=True).count())

    def run(self, new_event, cloners, shared_data):
        self._clone_nested_vc_rooms = False
        self._session_block_map = self._contrib_map = None
        if cloners >= {'sessions', 'contributions'}:
            self._clone_nested_vc_rooms = True
            self._session_block_map = shared_data['sessions']['session_block_map']
            self._contrib_map = shared_data['contributions']['contrib_map']
        with db.session.no_autoflush:
            self._clone_vc_rooms(new_event)
        db.session.flush()

    def _clone_vc_rooms(self, new_event):
        raise NotImplementedError('TODO adapt together with the rest of the VC module')
        for old_event_vc_room in VCRoomEventAssociation.find_for_event(self.event, include_hidden=True):
            event_vc_room = VCRoomEventAssociation(event_id=int(new_event.id),
                                                   link_type=old_event_vc_room.link_type,
                                                   link_id=old_event_vc_room.link_id,
                                                   show=old_event_vc_room.show,
                                                   data=old_event_vc_room.data)
            if event_vc_room.link_object is not None:
                event_vc_room.vc_room = old_event_vc_room.vc_room
                db.session.add(event_vc_room)
