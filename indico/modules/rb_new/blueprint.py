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
from indico.modules.rb_new.controllers.frontend import RHRoomBookingLanding
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('rooms_new', __name__, template_folder='templates', virtual_template_folder='rb_new',
                      url_prefix='/rooms-new')

# Frontend
_bp.add_url_rule('/', 'roombooking', RHRoomBookingLanding)
_bp.add_url_rule('/<path:path>', 'roombooking', RHRoomBookingLanding)

# Backend
_bp.add_url_rule('/api/rooms', 'available_rooms', backend.RHRoomBookingSearch)
_bp.add_url_rule('/api/map/aspects', 'default_aspects', backend.RHRoomBookingAspects)
_bp.add_url_rule('/api/buildings', 'buildings', backend.RHRoomBookingBuildings)
_bp.add_url_rule('/api/timeline', 'timeline', backend.RHRoomBookingTimeline)
