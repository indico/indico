# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import jsonify

from indico.modules.rb_new.controllers.backend import admin, blockings, bookings, locations, misc, rooms
from indico.modules.rb_new.controllers.frontend import RHRoomBooking
from indico.modules.rb_new.event import controllers as event
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('rooms_new', __name__, template_folder='templates', virtual_template_folder='rb_new',
                      url_prefix='/rooms-new')

# Frontend
_bp.add_url_rule('/', 'roombooking', RHRoomBooking)
_bp.add_url_rule('/<path:path>', 'roombooking', RHRoomBooking)
_bp.add_url_rule('/rooms-sprite-<version>.jpg', 'sprite', misc.RHRoomsSprite)
_bp.add_url_rule('/rooms-sprite.jpg', 'sprite', misc.RHRoomsSprite)
_bp.add_url_rule('/rooms/<int:room_id>.jpg', 'room_photo', rooms.RHRoomPhoto)

# General backend
_bp.add_url_rule('/api/<path:path>', '404', lambda path: (jsonify(), 404))
_bp.add_url_rule('/api/config', 'config', misc.RHConfig)
_bp.add_url_rule('/api/stats', 'stats', misc.RHStats)
_bp.add_url_rule('/api/map-areas', 'map_areas', misc.RHMapAreas)
_bp.add_url_rule('/api/equipment', 'equipment_types', misc.RHEquipmentTypes)
_bp.add_url_rule('/api/locations', 'locations', locations.RHLocations)
_bp.add_url_rule('/api/link-info/<any(event,contribution,session_block):type>/<int:id>', 'linked_object_data',
                 bookings.RHLinkedObjectData)
_bp.add_url_rule('/api/events', 'events', bookings.RHMatchingEvents)


# Rooms
_bp.add_url_rule('/api/rooms/', 'rooms', rooms.RHRooms)
_bp.add_url_rule('/api/rooms/permissions', 'rooms_permissions', rooms.RHRoomsPermissions)
_bp.add_url_rule('/api/rooms/search', 'search_rooms', rooms.RHSearchRooms)
_bp.add_url_rule('/api/rooms/<int:room_id>', 'room', rooms.RHRoom)
_bp.add_url_rule('/api/rooms/<int:room_id>/availability', 'room_availability', rooms.RHRoomAvailability)
_bp.add_url_rule('/api/rooms/<int:room_id>/attributes', 'room_attributes', rooms.RHRoomAttributes)
_bp.add_url_rule('/api/rooms/<int:room_id>/timeline', 'timeline', bookings.RHTimeline)
_bp.add_url_rule('/api/rooms/<int:room_id>/stats', 'room_stats', rooms.RHRoomStats)
_bp.add_url_rule('/api/rooms/<int:room_id>/availability/simple', 'check_room_available', rooms.RHCheckRoomAvailable)
_bp.add_url_rule('/api/suggestions', 'suggestions', bookings.RHRoomSuggestions)

# User
_bp.add_url_rule('/api/user/', 'user_info', misc.RHUserInfo)
_bp.add_url_rule('/api/user/favorite-rooms/', 'favorite_rooms', rooms.RHRoomFavorites)
_bp.add_url_rule('/api/user/favorite-rooms/<int:room_id>', 'favorite_rooms', rooms.RHRoomFavorites,
                 methods=('PUT', 'DELETE'))

# Calendar/timeline
_bp.add_url_rule('/api/calendar', 'calendar', bookings.RHCalendar, methods=('GET', 'POST'))
_bp.add_url_rule('/api/timeline', 'timeline', bookings.RHTimeline, methods=('GET', 'POST'))

# Bookings
_bp.add_url_rule('/api/booking/create', 'create_booking', bookings.RHCreateBooking, methods=('POST',))
_bp.add_url_rule('/api/bookings/active', 'active_bookings', bookings.RHActiveBookings, methods=('POST',))
_bp.add_url_rule('/api/bookings/<int:booking_id>', 'booking_details', bookings.RHBookingDetails)
_bp.add_url_rule('/api/bookings/<int:booking_id>', 'delete_booking', bookings.RHDeleteBooking, methods=('DELETE',))
_bp.add_url_rule('/api/bookings/<int:booking_id>', 'update_booking', bookings.RHUpdateBooking, methods=('PATCH',))
_bp.add_url_rule('/api/bookings/<int:booking_id>/<any(approve,reject,cancel):action>', 'booking_state_actions',
                 bookings.RHBookingStateActions, methods=('POST',))
_bp.add_url_rule('/api/bookings/mine', 'my_bookings', bookings.RHMyUpcomingBookings)
_bp.add_url_rule('/api/bookings/<int:booking_id>/<date>/<any(reject,cancel):action>',
                 'booking_occurrence_state_actions', bookings.RHBookingOccurrenceStateActions, methods=('POST',))

# Blockings
_bp.add_url_rule('/api/blockings/', 'blockings', blockings.RHRoomBlockings)
_bp.add_url_rule('/api/blockings/', 'create_blocking', blockings.RHCreateRoomBlocking, methods=('POST',))
_bp.add_url_rule('/api/blockings/<int:blocking_id>', 'blocking', blockings.RHRoomBlocking)
_bp.add_url_rule('/api/blockings/<int:blocking_id>', 'update_blocking', blockings.RHUpdateRoomBlocking,
                 methods=('PATCH',))
_bp.add_url_rule('/api/blockings/<int:blocking_id>/rooms/<int:room_id>/<any(accept,reject):action>',
                 'blocking_actions', blockings.RHBlockedRoomAction, methods=('POST',))
_bp.add_url_rule('/api/blockings/<int:blocking_id>', 'delete_blocking', blockings.RHDeleteBlocking, methods=('DELETE',))


# Administration
_bp.add_url_rule('/api/admin/locations', 'admin_locations', admin.RHLocations)
_bp.add_url_rule('/api/admin/equipment-types', 'admin_equipment_types', admin.RHEquipmentTypes, methods=('GET', 'POST'))
_bp.add_url_rule('/api/admin/equipment-types/<int:equipment_type_id>', 'admin_equipment_types', admin.RHEquipmentTypes,
                 methods=('GET', 'DELETE', 'PATCH'))
_bp.add_url_rule('/api/admin/features', 'admin_features', admin.RHFeatures, methods=('GET', 'POST'))
_bp.add_url_rule('/api/admin/features/<int:feature_id>', 'admin_features', admin.RHFeatures,
                 methods=('GET', 'DELETE', 'PATCH'))
_bp.add_url_rule('/api/admin/attributes', 'admin_attributes', admin.RHAttributes, methods=('GET', 'POST'))
_bp.add_url_rule('/api/admin/attributes/<int:attribute_id>', 'admin_attributes', admin.RHAttributes,
                 methods=('GET', 'DELETE', 'PATCH'))
_bp.add_url_rule('/api/admin/rooms/<int:room_id>', 'admin_room', admin.RHRoom)
_bp.add_url_rule('/api/admin/rooms/<int:room_id>', 'admin_update_room', admin.RHRoomUpdate, methods=('PATCH',))
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/equipment', 'admin_room_equipment', admin.RHRoomEquipment)
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/equipment', 'admin_update_room_equipment', admin.RHRoomEquipmentUpdate,
                 methods=('POST',))
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/attributes', 'admin_room_attributes', admin.RHRoomAttributes)
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/attributes', 'admin_update_room_attributes',
                 admin.RHRoomAttributesUpdate, methods=('POST',))
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/availability', 'admin_room_availability', admin.RHRoomAvailability)
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/availability', 'admin_update_room_availability', admin.RHRoomAvailabilityUpdate,
                 methods=('POST',))
_bp.add_url_rule('/api/admin/rooms/<int:room_id>/image', 'admin_room_image', admin.RHRoomImage)


# Event linking
_bp.add_url_rule('!/event/<confId>/manage/rooms/', 'event_booking_list', event.RHEventBookingList)
_bp.add_url_rule('!/event/<confId>/manage/rooms/linking/contributions', 'event_linkable_contributions',
                 event.RHListLinkableContributions)
_bp.add_url_rule('!/event/<confId>/manage/rooms/linking/session-blocks', 'event_linkable_session_blocks',
                 event.RHListLinkableSessionBlocks)

