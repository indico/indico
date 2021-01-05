# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import LocationWidget


class IndicoLocationField(JSONField):
    CAN_POPULATE = True
    widget = LocationWidget()

    def __init__(self, *args, **kwargs):
        from indico.modules.rb.models.locations import Location
        self.edit_address = kwargs.pop('edit_address', True)
        self.allow_location_inheritance = kwargs.pop('allow_location_inheritance', True)
        self.locations = (Location.query
                          .filter_by(is_deleted=False)
                          .options(joinedload('rooms'))
                          .order_by(db.func.lower(Location.name))
                          .all())
        super(IndicoLocationField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        from indico.modules.rb.models.locations import Location
        from indico.modules.rb.models.rooms import Room
        super(IndicoLocationField, self).process_formdata(valuelist)
        self.data['room'] = Room.get(int(self.data['room_id'])) if self.data.get('room_id') else None
        self.data['venue'] = (Location.get(int(self.data['venue_id']), is_deleted=False)
                              if self.data.get('venue_id')
                              else None)
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
