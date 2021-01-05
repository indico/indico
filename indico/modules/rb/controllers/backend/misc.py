# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import date, datetime, time, timedelta
from io import BytesIO

from flask import jsonify, redirect, request, session
from sqlalchemy.orm import joinedload

from indico.core.config import config
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.permissions import get_permissions_info
from indico.modules.legal import legal_settings
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.backend.common import _cache
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.map_areas import MapArea
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.schemas import EquipmentTypeSchema, map_areas_schema, rb_user_schema
from indico.modules.rb.util import build_rooms_spritesheet
from indico.util.caching import memoize_redis
from indico.util.i18n import get_all_locales
from indico.util.string import sanitize_html
from indico.web.flask.util import send_file, url_for


class RHConfig(RHRoomBookingBase):
    def _process(self):
        tos_url = legal_settings.get('tos_url')
        tos_html = sanitize_html(legal_settings.get('tos')) or None
        privacy_policy_url = legal_settings.get('privacy_policy_url')
        privacy_policy_html = sanitize_html(legal_settings.get('privacy_policy')) or None
        if tos_url:
            tos_html = None
        if privacy_policy_url:
            privacy_policy_html = None
        return jsonify(rooms_sprite_token=unicode(_cache.get('rooms-sprite-token', '')),
                       languages=get_all_locales(),
                       tileserver_url=rb_settings.get('tileserver_url'),
                       grace_period=rb_settings.get('grace_period'),
                       managers_edit_rooms=rb_settings.get('managers_edit_rooms'),
                       help_url=config.HELP_URL,
                       contact_email=config.PUBLIC_SUPPORT_EMAIL,
                       has_tos=bool(tos_url or tos_html),
                       tos_html=tos_html,
                       has_privacy_policy=bool(privacy_policy_url or privacy_policy_html),
                       privacy_policy_html=privacy_policy_html)


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
            active_rooms=Room.query.filter_by(is_deleted=False).count(),
            buildings=Room.query.distinct(Room.building).filter_by(is_deleted=False).count(),
            pending_bookings=Reservation.query.filter(Reservation.is_pending, ~Reservation.is_archived).count(),
            bookings_today=bookings_today
        )


class RHMapAreas(RHRoomBookingBase):
    def _process(self):
        return map_areas_schema.jsonify(MapArea.query)


class RHEquipmentTypes(RHRoomBookingBase):
    def _get_equipment_types(self):
        res = (EquipmentType.query
               .add_columns(EquipmentType.rooms.any(~Room.is_deleted))
               .options(joinedload('features'))
               .order_by(EquipmentType.name)
               .all())
        used_ids = {eq.id for eq, used in res if used}
        schema = EquipmentTypeSchema(many=True, context={'used_ids': used_ids})
        return schema.dump(eq for eq, __ in res)

    def _process(self):
        return jsonify(self._get_equipment_types())


class RHPermissionTypes(RHRoomBookingBase):
    def _process(self):
        permissions, tree, default = get_permissions_info(Room)
        return jsonify(permissions=permissions, tree=tree, default=default)
