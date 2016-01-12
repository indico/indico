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


from __future__ import unicode_literals, division

from operator import attrgetter

from indico.modules.events.models.events import Event
from indico.util.console import cformat, verbose_iterator
from indico.util.string import fix_broken_string
from indico.util.struct.iterables import committing_iterator
from MaKaC.conference import _get_room_mapping

from indico_zodbimport import Importer, convert_to_unicode


class EventLocationsImporter(Importer):
    def has_data(self):
        return bool(Event.query
                    .filter(((Event.own_address != '') | (Event.own_room_name != '') | (Event.own_venue_name != '') |
                             Event.own_room_id.isnot(None)))
                    .count())

    def migrate(self):
        self.room_mapping = {key: room.id for key, room in _get_room_mapping().iteritems()}
        self.migrate_event_locations()

    def migrate_event_locations(self):
        self.print_step("Migrating event locations")
        for old_event in committing_iterator(self._iter_events()):
            custom_location = old_event.places[0] if getattr(old_event, 'places', None) else None
            custom_room = old_event.rooms[0] if getattr(old_event, 'rooms', None) else None
            location_name = None
            room_name = None
            rb_room = None
            updates = {}
            if custom_location:
                location_name = fix_broken_string(custom_location.name, True)
                if custom_location.address:
                    updates[Event.own_address] = fix_broken_string(custom_location.address, True)
            if custom_room:
                room_name = fix_broken_string(custom_room.name, True)
            if location_name and room_name:
                rb_room = self.room_mapping.get((location_name, room_name))
                if rb_room:
                    updates[Event.own_room_id] = rb_room
            # if we don't have a RB room set, use whatever location/room name we have
            if not rb_room:
                updates[Event.own_venue_name] = location_name or ''
                updates[Event.own_room_name] = room_name or ''
            if updates:
                Event.query.filter_by(id=int(old_event.id)).update(updates, synchronize_session=False)
                if not self.quiet:
                    self.print_success(repr(updates), event_id=old_event.id)

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        total = len(self.zodb_root['conferences'])
        if self.quiet:
            it = verbose_iterator(it, total, attrgetter('id'), attrgetter('title'))
        for old_event in self.flushing_iterator(it):
            yield old_event
