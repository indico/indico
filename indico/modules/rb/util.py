# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
from collections import namedtuple
from datetime import datetime, time, timedelta
from io import BytesIO
from operator import attrgetter

import pytz
from flask import current_app
from PIL import Image
from sqlalchemy import Date, cast
from sqlalchemy.orm import joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.legacy.common.cache import GenericCache
from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.events.timetable.util import find_latest_entry_end_dt
from indico.util.caching import memoize_request
from indico.util.date_time import now_utc, server_to_utc
from indico.util.string import crc32
from indico.util.struct.iterables import group_list


ROOM_PHOTO_DIMENSIONS = (290, 170)
TempReservationOccurrence = namedtuple('ReservationOccurrenceTmp', ('start_dt', 'end_dt', 'reservation'))
TempReservationConcurrentOccurrence = namedtuple('ReservationOccurrenceTmp', ('start_dt', 'end_dt', 'reservations'))
_cache = GenericCache('Rooms')


@memoize_request
def rb_check_user_access(user):
    """Check if the user has access to the room booking system."""
    from indico.modules.rb import rb_settings
    if rb_is_admin(user):
        return True
    if not rb_settings.acls.get('authorized_principals'):  # everyone has access
        return True
    return rb_settings.acls.contains_user('authorized_principals', user)


@memoize_request
def rb_is_admin(user):
    """Check if the user is a room booking admin."""
    from indico.modules.rb import rb_settings
    if user.is_admin:
        return True
    return rb_settings.acls.contains_user('admin_principals', user)


def build_rooms_spritesheet():
    from indico.modules.rb.models.rooms import Room
    image_width, image_height = ROOM_PHOTO_DIMENSIONS
    rooms = Room.query.filter(Room.photo).options(joinedload('photo')).all()
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
    token = crc32(value)
    _cache.set('rooms-sprite', value)
    _cache.set('rooms-sprite-mapping', mapping)
    _cache.set('rooms-sprite-token', token)
    return token


def get_resized_room_photo(room):
    photo = Image.open(BytesIO(room.photo.data)).resize(ROOM_PHOTO_DIMENSIONS, Image.ANTIALIAS)
    output = BytesIO()
    photo.save(output, 'JPEG')
    return output.getvalue()


def remove_room_spritesheet_photo(room):
    mapping = _cache.get('rooms-sprite-mapping')
    if not mapping or room.id not in mapping:
        return
    del mapping[room.id]
    _cache.set('rooms-sprite-mapping', mapping)


def group_by_occurrence_date(occurrences, sort_by=None):
    return group_list(occurrences, key=lambda obj: obj.start_dt.date(), sort_by=sort_by)


def serialize_occurrences(data):
    from indico.modules.rb.schemas import (reservation_occurrences_schema)
    return {dt.isoformat(): reservation_occurrences_schema.dump(data) for dt, data in data.iteritems()}


def serialize_blockings(data):
    from indico.modules.rb.schemas import (simple_blockings_schema)
    return {dt.isoformat(): simple_blockings_schema.dump(data) for dt, data in data.iteritems()}


def serialize_nonbookable_periods(data):
    from indico.modules.rb.schemas import (nonbookable_periods_schema)
    return {dt.isoformat(): nonbookable_periods_schema.dump(data) for dt, data in data.iteritems()}


def serialize_unbookable_hours(data):
    from indico.modules.rb.schemas import (bookable_hours_schema)
    return [bookable_hours_schema.dump(d) for d in data]


def serialize_concurrent_pre_bookings(data):
    from indico.modules.rb.schemas import (concurrent_pre_bookings_schema)
    return {dt.isoformat(): concurrent_pre_bookings_schema.dump(data) for dt, data in data.iteritems()}


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
    from indico.modules.rb import rb_settings

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
    from indico.modules.rb.operations.blockings import filter_blocked_rooms, get_rooms_blockings, group_blocked_rooms
    from indico.modules.rb.operations.bookings import (get_booking_occurrences, get_existing_room_occurrences,
                                                       group_blockings, group_nonbookable_periods)
    from indico.modules.rb.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
    from indico.modules.rb.schemas import reservation_details_schema, reservation_occurrences_schema_with_permissions

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
    other_bookings = get_existing_room_occurrences(booking.room, start_dt, end_dt, booking.repeat_frequency,
                                                   booking.repeat_interval, skip_booking_id=booking.id)
    blocked_rooms = get_rooms_blockings([booking.room], start_dt.date(), end_dt.date())
    overridable_blockings = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                     overridable_only=True,
                                                                     explicit=True)).get(booking.room.id, [])
    nonoverridable_blockings = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                        nonoverridable_only=True,
                                                                        explicit=True)).get(booking.room.id, [])
    nonbookable_periods = get_rooms_nonbookable_periods([booking.room], start_dt, end_dt).get(booking.room.id, [])
    nonbookable_periods_grouped = group_nonbookable_periods(nonbookable_periods, date_range)
    occurrences_by_type['other'] = serialize_occurrences(group_by_occurrence_date(other_bookings))
    occurrences_by_type['blockings'] = serialize_blockings(group_blockings(nonoverridable_blockings, date_range))
    occurrences_by_type['overridable_blockings'] = serialize_blockings(group_blockings(overridable_blockings,
                                                                                       date_range))
    occurrences_by_type['unbookable_hours'] = serialize_unbookable_hours(unbookable_hours)
    occurrences_by_type['nonbookable_periods'] = serialize_nonbookable_periods(nonbookable_periods_grouped)
    return booking_details


def serialize_availability(availability):
    for data in availability.viewvalues():
        data['blockings'] = serialize_blockings(data.get('blockings', {}))
        data['overridable_blockings'] = serialize_blockings(data.get('overridable_blockings', {}))
        data['nonbookable_periods'] = serialize_nonbookable_periods(data.get('nonbookable_periods', {}))
        data['unbookable_hours'] = serialize_unbookable_hours(data.get('unbookable_hours', {}))
        data['concurrent_pre_bookings'] = serialize_concurrent_pre_bookings(data.get('concurrent_pre_bookings', {}))
        data.update({k: serialize_occurrences(data[k]) if k in data else {}
                     for k in ('candidates', 'conflicting_candidates', 'pre_bookings', 'bookings', 'conflicts',
                               'pre_conflicts', 'rejections', 'cancellations')})
    return availability


def generate_spreadsheet_from_occurrences(occurrences):
    """Generate spreadsheet data from a given booking occurrence list.

    :param occurrences: The booking occurrences to include in the spreadsheet
    """
    headers = ['Room', 'Booking ID', 'Booked for', 'Reason', 'Occurrence start', 'Occurrence end']
    rows = [{'Room': occ.reservation.room.full_name,
             'Booking ID': occ.reservation.id,
             'Booked for': occ.reservation.booked_for_name,
             'Reason': occ.reservation.booking_reason,
             'Occurrence start': occ.start_dt,
             'Occurrence end': occ.end_dt}
            for occ in occurrences]
    return headers, rows


def _find_first_entry_start_dt(event, day):
    """Find the first timetable entry on a given day."""
    if not (event.start_dt_local.date() <= day <= event.end_dt_local.date()):
        raise ValueError("Day out of event bounds.")
    entries = event.timetable_entries.filter(TimetableEntry.parent_id.is_(None),
                                             cast(TimetableEntry.start_dt.astimezone(event.tzinfo), Date) == day).all()
    return min(entries, key=attrgetter('start_dt')).start_dt.astimezone(event.tzinfo) if entries else None


def _find_latest_entry_end_dt(event, day):
    dt = find_latest_entry_end_dt(event, day)
    if dt:
        return dt.astimezone(event.tzinfo)


def get_booking_params_for_event(event):
    """Get a set of RB interface parameters suitable for this event.

    These parameters can then be used to construct a URL that will lead to a
    pre-filled search that matches the start/end times for a given day.

    :param event: `Event` object
    """
    is_single_day = event.start_dt_local.date() == event.end_dt_local.date()
    params = {
        'link_type': 'event',
        'link_id': event.id,
        'text': '#{}'.format(event.room.id) if event.room else None,
    }
    all_times = {day: (_find_first_entry_start_dt(event, day), _find_latest_entry_end_dt(event, day))
                 for day in event.iter_days(tzinfo=event.tzinfo)}
    # if the timetable is empty on a given day, use (start_dt, end_dt) of the event
    all_times = [((day, (event.start_dt_local, event.end_dt_local)) if times[0] is None else (day, times))
                 for day, times in all_times.viewitems()]
    same_times = len(set(times for (_, times) in all_times)) == 1

    if is_single_day or same_times:
        params['sd'] = event.start_dt_local.date().isoformat()
        if event.start_dt_local.time() < event.end_dt_local.time():
            # if we have suitable times we provide enough data to immediately run a search.
            # XXX: if filtersAreSet also checked for times we could provide dates/recurrence
            # as well even when we don't know suitable times.. but that would require extra
            # code to handle the case of a custom RB interface where no times are used at all
            params.update({
                'ed': None if is_single_day else event.end_dt_local.date().isoformat(),
                'recurrence': 'single' if is_single_day else 'daily',
                'st': event.start_dt_local.strftime('%H:%M'),
                'et': event.end_dt_local.strftime('%H:%M'),
                'number': 1,
                'interval': 'week',
            })
        return {
            'type': 'same_times',
            'params': params
        }
    else:
        time_info = sorted([
            (day, {
                # if we have a proper start/end time, we provide all args to search
                'number': 1,
                'interval': 'week',
                'recurrence': 'single',
                'sd': day.isoformat(),
                'st': start.strftime('%H:%M'),
                'et': end.strftime('%H:%M')
            } if start.time() < end.time() else {
                # if not (empty days or event end time < event start time), we just
                # populate the day and let the user specify the times manually
                'sd': day.isoformat(),
            }) for day, (start, end) in all_times
        ])
        return {
            'type': 'mixed_times',
            'params': params,
            'time_info': time_info
        }


def get_prebooking_collisions(reservation):
    from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
    valid_occurrences = reservation.occurrences.filter(ReservationOccurrence.is_valid).all()
    return ReservationOccurrence.find_overlapping_with(reservation.room, valid_occurrences, reservation.id).all()
