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

from __future__ import unicode_literals, absolute_import

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.rb import Location, Room
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import LocationWidget


class IndicoLocationField(JSONField):
    CAN_POPULATE = True
    widget = LocationWidget()

    def __init__(self, *args, **kwargs):
        self.allow_location_inheritance = kwargs.pop('allow_location_inheritance', True)
        self.locations = Location.query.options(joinedload('rooms')).order_by(db.func.lower(Location.name)).all()
        super(IndicoLocationField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super(IndicoLocationField, self).process_formdata(valuelist)
        self.data['room'] = Room.get(int(self.data['room_id'])) if self.data.get('room_id') else None
        self.data['venue'] = Location.get(int(self.data['venue_id'])) if self.data.get('venue_id') else None
        self.data['source'] = self.object_data.get('source') if self.object_data else None

    def _value(self):
        if not self.data:
            return {}
        result = {
            'address': self.data.get('address', ''),
            'inheriting': self.data.get('inheriting', False),
        }
        if self.data.get('room'):
            result['room_id'] = self.data['room'].id
            result['room_name'] = self.data['room'].full_name
            result['venue_id'] = self.data['room'].location.id
            result['venue_name'] = self.data['room'].location.name
        elif self.data.get('room_name'):
            result['room_name'] = self.data['room_name']
        if self.data.get('venue'):
            result['venue_id'] = self.data['venue'].id
            result['venue_name'] = self.data['venue'].name
        elif self.data.get('venue_name'):
            result['venue_name'] = self.data['venue_name']
        return result
