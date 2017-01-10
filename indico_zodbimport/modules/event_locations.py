# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.orm import lazyload, joinedload

from indico.modules.events.models.events import Event
from indico.modules.rb import Location, Room
from indico.util.console import verbose_iterator
from indico.util.string import fix_broken_string
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


def _get_room_mapping():
    return {(r.location.name, r.name): r for r in Room.query.options(lazyload(Room.owner), joinedload(Room.location))}


class EventLocationsImporter(Importer):
    def has_data(self):
        return (Event.query
                .filter(((Event.own_address != '') | (Event.own_room_name != '') | (Event.own_venue_name != '') |
                         Event.own_room_id.isnot(None)))
                .has_rows())

    def migrate(self):
        self.venue_mapping = {location.name: location.id for location in Location.query}
        self.room_mapping = {key: (room.location_id, room.id) for key, room in _get_room_mapping().iteritems()}
        self.migrate_event_locations()

    def migrate_event_locations(self):
        self.print_step("Migrating event locations")
        for old_event in committing_iterator(self._iter_events()):
            custom_location = old_event.places[0] if getattr(old_event, 'places', None) else None
            custom_room = old_event.rooms[0] if getattr(old_event, 'rooms', None) else None
            location_name = None
            room_name = None
            has_room = False
            updates = {}
            if custom_location:
                location_name = convert_to_unicode(fix_broken_string(custom_location.name, True))
                if custom_location.address:
                    updates[Event.own_address] = convert_to_unicode(fix_broken_string(custom_location.address, True))
            if custom_room:
                room_name = convert_to_unicode(fix_broken_string(custom_room.name, True))
            if location_name and room_name:
                mapping = self.room_mapping.get((location_name, room_name))
                if mapping:
                    has_room = True
                    updates[Event.own_venue_id] = mapping[0]
                    updates[Event.own_room_id] = mapping[1]
            # if we don't have a RB room set, use whatever location/room name we have
            if not has_room:
                venue_id = self.venue_mapping.get(location_name)
                if venue_id is not None:
                    updates[Event.own_venue_id] = venue_id
                    updates[Event.own_venue_name] = ''
                else:
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
            it = verbose_iterator(it, total, attrgetter('id'), lambda x: x.__dict__.get('title', ''))
        for old_event in self.flushing_iterator(it):
            yield old_event
