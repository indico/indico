# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.modules.events.cloning import EventCloner
from indico.modules.vc import VCRoomEventAssociation, VCRoomLinkType, get_vc_plugins
from indico.util.i18n import _


class VCCloner(EventCloner):
    name = 'vc'
    friendly_name = _('Videoconference rooms')
    uses = {'sessions', 'contributions'}
    is_default = True

    @property
    def is_visible(self):
        return bool(get_vc_plugins())

    @property
    def is_available(self):
        return VCRoomEventAssociation.find_for_event(self.old_event, include_hidden=True).has_rows()

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
        for old_event_vc_room in self.old_event.all_vc_room_associations:
            link_object = None
            if old_event_vc_room.link_type == VCRoomLinkType.event:
                link_object = new_event
            elif old_event_vc_room.link_type == VCRoomLinkType.contribution and self._contrib_map is not None:
                link_object = self._contrib_map[old_event_vc_room.link_object]
            elif old_event_vc_room.link_type == VCRoomLinkType.block and self._session_block_map is not None:
                link_object = self._session_block_map[old_event_vc_room.link_object]
            if link_object is None:
                continue
            event_vc_room = VCRoomEventAssociation(show=old_event_vc_room.show, data=old_event_vc_room.data,
                                                   link_object=link_object)
            old_event_vc_room.vc_room.events.append(event_vc_room)
