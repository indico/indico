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

from indico.core.marshmallow import mm
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.rooms import Room


class RoomSchema(mm.ModelSchema):
    class Meta:
        model = Room
        fields = ('id', 'name', 'capacity', 'building', 'floor', 'number', 'is_public', 'location_name', 'has_vc',
                  'has_projector', 'has_webcast_recording', 'large_photo_url', 'full_name')


class AspectSchema(mm.ModelSchema):
    class Meta:
        model = Aspect
        fields = ('top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude')


rooms_schema = RoomSchema(many=True)
aspect_schema = AspectSchema()
