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

import os
from collections import namedtuple
from datetime import datetime, time, timedelta
from io import BytesIO

import pytz
from flask import current_app
from PIL import Image

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.legacy.common.cache import GenericCache
from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.rb import rb_settings
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.operations.blockings import filter_blocked_rooms, get_rooms_blockings, group_blocked_rooms
from indico.modules.rb_new.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
from indico.modules.rb_new.schemas import (bookable_hours_schema, nonbookable_periods_schema,
                                           reservation_details_schema, reservation_occurrences_schema,
                                           reservation_occurrences_schema_with_permissions, simple_blockings_schema)
from indico.util.date_time import now_utc, server_to_utc
from indico.util.string import crc32
from indico.util.struct.iterables import group_list


ROOM_PHOTO_DIMENSIONS = (290, 170)
TempReservationOccurrence = namedtuple('ReservationOccurrenceTmp', ('start_dt', 'end_dt', 'reservation'))
_cache = GenericCache('Rooms')


def build_rooms_spritesheet():
    image_width, image_height = ROOM_PHOTO_DIMENSIONS
    rooms = Room.query.filter(Room.photo).all()
    room_count = len(rooms)
    sprite_width = (image_width * (room_count + 1))  # +1 for the placeholder
    sprite_height = image_height
    sprite = Image.new(mode='RGB', size=(sprite_width, sprite_height), color=(0, 0, 0))
    # Placeholder image at position 0
    no_photo_path = 'web/static/images/rooms/large_photos/NoPhoto.jpg'
    no_photo_image = Image.open(os.path.join(current_app.root_path, no_photo_path))
    image = no_photo_image.resize(ROOM_PHOTO_DIMENSIONS, Image.ANTIALIAS)
    sprite.paste(image, (0, 0))
    mapping = {}
    for count, room in enumerate(rooms, start=1):
        location = image_width * count
        image = Image.open(BytesIO(room.photo.data)).resize(ROOM_PHOTO_DIMENSIONS, Image.ANTIALIAS)
        sprite.paste(image, (location, 0))
        mapping[room.id] = count

    output = BytesIO()
    sprite.save(output, 'JPEG')
    value = output.getvalue()
    _cache.set('rooms-sprite', value)
    _cache.set('rooms-sprite-mapping', mapping)
    _cache.set('rooms-sprite-token', crc32(value))


def group_by_occurrence_date(occurrences, sort_by=None):
    return group_list(occurrences, key=lambda obj: obj.start_dt.date(), sort_by=sort_by)


def serialize_occurrences(data):
    return {dt.isoformat(): reservation_occurrences_schema.dump(data) for dt, data in data.iteritems()}


def serialize_blockings(data):
    return {dt.isoformat(): simple_blockings_schema.dump(data) for dt, data in data.iteritems()}


def serialize_nonbookable_periods(data):
    return {dt.isoformat(): nonbookable_periods_schema.dump(data) for dt, data in data.iteritems()}


def serialize_unbookable_hours(data):
    return [bookable_hours_schema.dump(d) for d in data]


def get_linked_object(type_, id_):
    if type_ == LinkType.event:
        return Event.get(id_, is_deleted=False)
    elif type_ == LinkType.contribution:
        return (Contribution.query
                .filter(Contribution.id == id_,
                        ~Contribution.is_deleted,
                        Contribution.event.has(is_deleted=False))
                .first())
    elif type_ == LinkType.session_block:
        return (SessionBlock.query
                .filter(SessionBlock.id == id_,
                        SessionBlock.session.has(db.and_(~Session.is_deleted,
                                                         Session.event.has(is_deleted=False))))
                .first())


def is_booking_start_within_grace_period(start_dt, user, allow_admin=False):
    if allow_admin and rb_is_admin(user):
        return True

    default_tz = pytz.timezone(config.DEFAULT_TIMEZONE)
    start_dt_localized = default_tz.localize(start_dt)
    grace_period = rb_settings.get('grace_period')
    if grace_period is None:
        today = server_to_utc(datetime.now()).astimezone(default_tz).date()
        return start_dt_localized.date() >= today

    start_dt_utc = start_dt_localized.astimezone(pytz.utc)
    grace_period = timedelta(hours=grace_period)
    return start_dt_utc >= now_utc() - grace_period


def serialize_booking_details(booking):
    from indico.modules.rb_new.operations.bookings import (get_booking_occurrences, group_blockings,
                                                           group_nonbookable_periods, get_room_bookings)

    attributes = reservation_details_schema.dump(booking)
    date_range, occurrences = get_booking_occurrences(booking)
    booking_details = dict(attributes)
    occurrences_by_type = dict(bookings={}, cancellations={}, rejections={}, other={}, blockings={},
                               unbookable_hours={}, nonbookable_periods={}, overridable_blockings={})
    booking_details['occurrences'] = occurrences_by_type
    booking_details['date_range'] = [dt.isoformat() for dt in date_range]
    for dt, [occ] in occurrences.iteritems():
        serialized_occ = reservation_occurrences_schema_with_permissions.dump([occ])
        if occ.is_cancelled:
            occurrences_by_type['cancellations'][dt.isoformat()] = serialized_occ
        elif occ.is_rejected:
            occurrences_by_type['rejections'][dt.isoformat()] = serialized_occ
        occurrences_by_type['bookings'][dt.isoformat()] = serialized_occ if occ.is_valid else []

    start_dt = datetime.combine(booking.start_dt, time.min)
    end_dt = datetime.combine(booking.end_dt, time.max)
    unbookable_hours = get_rooms_unbookable_hours([booking.room]).get(booking.room.id, [])
    blocked_rooms = get_rooms_blockings([booking.room], start_dt.date(), end_dt.date())
    overridable_blockings = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                     overridable_only=True,
                                                                     explicit=True)).get(booking.room.id, [])
    nonoverridable_blockings = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                        nonoverridable_only=True,
                                                                        explicit=True)).get(booking.room.id, [])
    nonbookable_periods = get_rooms_nonbookable_periods([booking.room], start_dt, end_dt).get(booking.room.id, [])
    nonbookable_periods_grouped = group_nonbookable_periods(nonbookable_periods, date_range)
    occurrences_by_type['other'] = get_room_bookings(booking.room, start_dt, end_dt, skip_booking_id=booking.id)
    occurrences_by_type['blockings'] = serialize_blockings(group_blockings(nonoverridable_blockings, date_range))
    occurrences_by_type['overridable_blockings'] = serialize_blockings(group_blockings(overridable_blockings,
                                                                                       date_range))
    occurrences_by_type['unbookable_hours'] = serialize_unbookable_hours(unbookable_hours)
    occurrences_by_type['nonbookable_periods'] = serialize_nonbookable_periods(nonbookable_periods_grouped)
    return booking_details


def serialize_availability(availability):
    for data in availability.viewvalues():
        data['blockings'] = serialize_blockings(data.get('blockings', {}))
        data['nonbookable_periods'] = serialize_nonbookable_periods(data.get('nonbookable_periods', {}))
        data['unbookable_hours'] = serialize_unbookable_hours(data.get('unbookable_hours', {}))
        data.update({k: serialize_occurrences(data[k]) if k in data else {}
                     for k in ('candidates', 'conflicting_candidates', 'pre_bookings', 'bookings', 'conflicts',
                               'pre_conflicts', 'rejections', 'cancellations')})
    return availability
