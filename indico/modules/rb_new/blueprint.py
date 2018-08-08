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

from indico.modules.rb_new.controllers import backend
from indico.modules.rb_new.controllers.frontend import RHLanding
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('rooms_new', __name__, template_folder='templates', virtual_template_folder='rb_new',
                      url_prefix='/rooms-new')

# Frontend
_bp.add_url_rule('/', 'roombooking', RHLanding)
_bp.add_url_rule('/<path:path>', 'roombooking', RHLanding)

# Backend
_bp.add_url_rule('/api/rooms', 'available_rooms', backend.RHSearchRooms)
_bp.add_url_rule('/api/room/<int:room_id>', 'room_details', backend.RHRoomDetails)
_bp.add_url_rule('/api/map/rooms', 'map_rooms', backend.RHSearchMapRooms)
_bp.add_url_rule('/api/user/', 'user_info', backend.RHUserInfo)
_bp.add_url_rule('/api/user/favorite-rooms/', 'favorite_rooms', backend.RHRoomFavorites)
_bp.add_url_rule('/api/user/favorite-rooms/<int:room_id>', 'favorite_rooms', backend.RHRoomFavorites,
                 methods=('PUT', 'DELETE'))
_bp.add_url_rule('/api/map/aspects', 'default_aspects', backend.RHAspects)
_bp.add_url_rule('/api/buildings', 'buildings', backend.RHBuildings)
_bp.add_url_rule('/api/timeline', 'timeline', backend.RHTimeline)
_bp.add_url_rule('/api/equipment', 'equipment_types', backend.RHEquipmentTypes)
_bp.add_url_rule('/api/booking/create', 'create_booking', backend.RHCreateBooking,
                 methods=('POST',))
_bp.add_url_rule('/api/suggestions', 'suggestions', backend.RHRoomSuggestions)
_bp.add_url_rule('/api/blockings', 'blockings', backend.RHRoomBlockings)
_bp.add_url_rule('/api/locations', 'locations', backend.RHLocations)
