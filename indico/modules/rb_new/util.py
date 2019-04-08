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
from datetime import datetime, timedelta
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
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.schemas import (bookable_hours_schema, nonbookable_periods_schema,
                                           reservation_occurrences_schema, simple_blockings_schema)
from indico.util.date_time import now_utc
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
    start_dt_utc = default_tz.localize(start_dt).astimezone(pytz.utc)
    return start_dt_utc >= now_utc() - timedelta(hours=1)
