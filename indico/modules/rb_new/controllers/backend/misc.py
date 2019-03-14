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

from datetime import date, datetime, time, timedelta
from io import BytesIO

from flask import jsonify, redirect, request, session
from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.map_areas import MapArea
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.controllers.backend.common import _cache
from indico.modules.rb_new.schemas import equipment_type_schema, map_areas_schema, rb_user_schema
from indico.modules.rb_new.util import build_rooms_spritesheet
from indico.util.caching import memoize_redis
from indico.util.i18n import get_all_locales
from indico.web.flask.util import send_file, url_for


class RHConfig(RHRoomBookingBase):
    def _process(self):
        return jsonify(rooms_sprite_token=unicode(_cache.get('rooms-sprite-token', '')),
                       languages=get_all_locales(),
                       tileserver_url=rb_settings.get('tileserver_url'))


class RHUserInfo(RHRoomBookingBase):
    def _process(self):
        data = rb_user_schema.dump(session.user)
        data['language'] = session.lang
        return jsonify(data)


class RHRoomsSprite(RHRoomBookingBase):
    def _process(self):
        sprite_mapping = _cache.get('rooms-sprite-mapping')
        if sprite_mapping is None:
            build_rooms_spritesheet()
        if 'version' not in request.view_args:
            return redirect(url_for('.sprite', version=_cache.get('rooms-sprite-token')))
        photo_data = _cache.get('rooms-sprite')
        return send_file('rooms-sprite.jpg', BytesIO(photo_data), 'image/jpeg', no_cache=False, cache_timeout=365*86400)


class RHStats(RHRoomBookingBase):
    def _process(self):
        return self._get_stats(date.today())

    @staticmethod
    @memoize_redis(3600)
    def _get_stats(date):
        today_dt = datetime.combine(date, time())
        bookings_today = (ReservationOccurrence.query
                          .filter(ReservationOccurrence.is_valid,
                                  db_dates_overlap(ReservationOccurrence,
                                                   'start_dt', today_dt,
                                                   'end_dt', today_dt + timedelta(days=1)))
                          .count())
        return jsonify(
            active_rooms=Room.query.filter_by(is_active=True).count(),
            buildings=Room.query.distinct(Room.building).filter_by(is_active=True).count(),
            pending_bookings=Reservation.query.filter(Reservation.is_pending, ~Reservation.is_archived).count(),
            bookings_today=bookings_today
        )


class RHMapAreas(RHRoomBookingBase):
    def _process(self):
        return jsonify(map_areas_schema.dump(MapArea.query))


class RHEquipmentTypes(RHRoomBookingBase):
    def _get_equipment_types(self):
        query = (EquipmentType.query
                 .filter(EquipmentType.rooms.any(Room.is_active))
                 .options(joinedload('features'))
                 .order_by(EquipmentType.name))
        return equipment_type_schema.dump(query, many=True)

    def _process(self):
        return jsonify(self._get_equipment_types())
