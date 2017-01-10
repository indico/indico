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

from datetime import datetime

import icalendar
import pytz
from babel.dates import get_timezone
from sqlalchemy import Time, Date, or_
from sqlalchemy.sql import cast
from werkzeug.datastructures import OrderedMultiDict, MultiDict

from indico.core.config import Config
from indico.core.db import db
from indico.core.errors import IndicoError
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.rb.util import rb_check_user_access
from indico.modules.rb.models.reservations import Reservation, RepeatMapping, RepeatFrequency, ConflictingOccurrences
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.util.date_time import utc_to_server
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.metadata import ical
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.util import get_query_parameter


class RoomBookingHookBase(HTTPAPIHook):
    GUEST_ALLOWED = False

    def _getParams(self):
        super(RoomBookingHookBase, self)._getParams()
        self._fromDT = utc_to_server(self._fromDT.astimezone(pytz.utc)).replace(tzinfo=None) if self._fromDT else None
        self._toDT = utc_to_server(self._toDT.astimezone(pytz.utc)).replace(tzinfo=None) if self._toDT else None
        self._occurrences = _yesno(get_query_parameter(self._queryParams, ['occ', 'occurrences'], 'no'))

    def _hasAccess(self, aw):
        return Config.getInstance().getIsRoomBookingActive() and rb_check_user_access(aw.getUser())


@HTTPAPIHook.register
class RoomHook(RoomBookingHookBase):
    # e.g. /export/room/CERN/23.json
    TYPES = ('room',)
    RE = r'(?P<location>[\w\s]+)/(?P<idlist>\w+(?:-[\w\s]+)*)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 500,
        'reservations': 100
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(RoomHook, self)._getParams()
        self._location = self._pathParams['location']
        self._ids = map(int, self._pathParams['idlist'].split('-'))
        if self._detail not in {'rooms', 'reservations'}:
            raise HTTPAPIError('Invalid detail level: %s' % self._detail, 400)

    def export_room(self, aw):
        loc = Location.find_first(name=self._location)
        if loc is None:
            return

        # Retrieve rooms
        rooms_data = list(Room.get_with_data('vc_equipment', 'non_vc_equipment',
                                             filters=[Room.id.in_(self._ids), Room.location_id == loc.id]))

        # Retrieve reservations
        reservations = None
        if self._detail == 'reservations':
            reservations = OrderedMultiDict(_export_reservations(self, True, False, [
                Reservation.room_id.in_(x['room'].id for x in rooms_data)
            ]))

        for result in rooms_data:
            yield _serializable_room(result, reservations)


@HTTPAPIHook.register
class RoomNameHook(RoomBookingHookBase):
    # e.g. /export/roomName/CERN/pump.json
    GUEST_ALLOWED = True
    TYPES = ('roomName', )
    RE = r'(?P<location>[\w\s]+)/(?P<room_name>[\w\s\-]+)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 500
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(RoomNameHook, self)._getParams()
        self._location = self._pathParams['location']
        self._room_name = self._pathParams['room_name']

    def _hasAccess(self, aw):
        # Access to RB data (no reservations) is public
        return Config.getInstance().getIsRoomBookingActive()

    def export_roomName(self, aw):
        loc = Location.find_first(name=self._location)
        if loc is None:
            return

        search_str = '%{}%'.format(self._room_name)
        rooms_data = Room.get_with_data(
            'vc_equipment', 'non_vc_equipment', filters=[
                Room.location_id == loc.id,
                or_((Room.building + '-' + Room.floor + '-' + Room.number).ilike(search_str),
                    Room.name.ilike(search_str))
            ])

        for result in rooms_data:
            yield _serializable_room(result)


@HTTPAPIHook.register
class ReservationHook(RoomBookingHookBase):
    # e.g. /export/reservation/CERN.json
    TYPES = ('reservation', )
    RE = r'(?P<loclist>[\w\s]+(?:-[\w\s]+)*)'
    DEFAULT_DETAIL = 'reservations'
    MAX_RECORDS = {
        'reservations': 100
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml', 'ics')

    @property
    def serializer_args(self):
        return {'ical_serializer': _ical_serialize_reservation}

    def _getParams(self):
        super(ReservationHook, self)._getParams()
        self._locations = self._pathParams['loclist'].split('-')

    def export_reservation(self, aw):
        locations = Location.find_all(Location.name.in_(self._locations))
        if not locations:
            return

        for room_id, reservation in _export_reservations(self, False, True):
            yield reservation


@HTTPAPIHook.register
class BookRoomHook(HTTPAPIHook):
    PREFIX = 'api'
    TYPES = ('roomBooking',)
    RE = r'bookRoom'
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json', 'xml')
    COMMIT = True
    HTTP_POST = True

    def _getParams(self):
        super(BookRoomHook, self)._getParams()
        self._fromDT = utc_to_server(self._fromDT.astimezone(pytz.utc)).replace(tzinfo=None) if self._fromDT else None
        self._toDT = utc_to_server(self._toDT.astimezone(pytz.utc)).replace(tzinfo=None) if self._toDT else None
        if not self._fromDT or not self._toDT or self._fromDT.date() != self._toDT.date():
            raise HTTPAPIError('from/to must be on the same day')
        elif self._fromDT >= self._toDT:
            raise HTTPAPIError('to must be after from')
        elif self._fromDT < datetime.now():
            raise HTTPAPIError('You cannot make bookings in the past')

        username = get_query_parameter(self._queryParams, 'username')
        if not username:
            raise HTTPAPIError('No username provided')
        users = User.find_all(~User.is_deleted, Identity.identifier == username)
        if not users:
            raise HTTPAPIError('Username does not exist')
        elif len(users) != 1:
            raise HTTPAPIError('Ambiguous username ({} users found)'.format(len(users)))
        user = users[0]

        self._params = {
            'room_id': get_query_parameter(self._queryParams, 'roomid'),
            'reason': get_query_parameter(self._queryParams, 'reason'),
            'booked_for': user,
            'from': self._fromDT,
            'to': self._toDT
        }
        missing = [key for key, val in self._params.iteritems() if not val]
        if missing:
            raise HTTPAPIError('Required params missing: {}'.format(', '.join(missing)))
        self._room = Room.get(self._params['room_id'])
        if not self._room:
            raise HTTPAPIError('A room with this ID does not exist')

    def _hasAccess(self, aw):
        if not Config.getInstance().getIsRoomBookingActive() or not rb_check_user_access(aw.getUser()):
            return False
        if self._room.can_be_booked(aw.getUser()):
            return True
        elif self._room.can_be_prebooked(aw.getUser()):
            raise HTTPAPIError('The API only supports direct bookings but this room only allows pre-bookings.')
        return False

    def api_roomBooking(self, aw):
        data = MultiDict({
            'start_dt': self._params['from'],
            'end_dt': self._params['to'],
            'repeat_frequency': RepeatFrequency.NEVER,
            'repeat_interval': 0,
            'room_id': self._room.id,
            'booked_for_user': self._params['booked_for'],
            'contact_email': self._params['booked_for'].email,
            'contact_phone': self._params['booked_for'].phone,
            'booking_reason': self._params['reason']
        })
        try:
            reservation = Reservation.create_from_data(self._room, data, aw.getUser())
        except ConflictingOccurrences:
            raise HTTPAPIError('Failed to create the booking due to conflicts with other bookings')
        except IndicoError as e:
            raise HTTPAPIError('Failed to create the booking: {}'.format(e))
        db.session.add(reservation)
        db.session.flush()
        return {'reservationID': reservation.id}


def _export_reservations(hook, limit_per_room, include_rooms, extra_filters=None):
    """Exports reservations.

    :param hook: The HTTPAPIHook instance
    :param limit_per_room: Should the limit/offset be applied per room
    :param include_rooms: Should reservations include room information
    """
    filters = list(extra_filters) if extra_filters else []
    if hook._fromDT and hook._toDT:
        filters.append(cast(Reservation.start_dt, Date) <= hook._toDT.date())
        filters.append(cast(Reservation.end_dt, Date) >= hook._fromDT.date())
        filters.append(cast(Reservation.start_dt, Time) <= hook._toDT.time())
        filters.append(cast(Reservation.end_dt, Time) >= hook._fromDT.time())
    elif hook._toDT:
        filters.append(cast(Reservation.end_dt, Date) <= hook._toDT.date())
        filters.append(cast(Reservation.end_dt, Time) <= hook._toDT.time())
    elif hook._fromDT:
        filters.append(cast(Reservation.start_dt, Date) >= hook._fromDT.date())
        filters.append(cast(Reservation.start_dt, Time) >= hook._fromDT.time())
    filters += _get_reservation_state_filter(hook._queryParams)
    occurs = [datetime.strptime(x, '%Y-%m-%d').date()
              for x in filter(None, get_query_parameter(hook._queryParams, ['occurs'], '').split(','))]
    data = ['vc_equipment']
    if hook._occurrences:
        data.append('occurrences')
    order = {
        'start': Reservation.start_dt,
        'end': Reservation.end_dt
    }.get(hook._orderBy, Reservation.start_dt)
    if hook._descending:
        order = order.desc()
    reservations_data = Reservation.get_with_data(*data, filters=filters, limit=hook._limit, offset=hook._offset,
                                                  order=order, limit_per_room=limit_per_room, occurs_on=occurs)
    for result in reservations_data:
        yield result['reservation'].room_id, _serializable_reservation(result, include_rooms)


def _serializable_room(room_data, reservations=None):
    """Serializable room data

    :param room_data: Room data
    :param reservations: MultiDict mapping for room id => reservations
    """
    data = room_data['room'].to_serializable('__api_public__')
    data['_type'] = 'Room'
    data['avc'] = bool(room_data['vc_equipment'])
    data['vcList'] = room_data['vc_equipment']
    data['equipment'] = room_data['non_vc_equipment']
    if reservations is not None:
        data['reservations'] = reservations.getlist(room_data['room'].id)
    return data


def _serializable_room_minimal(room):
    """Serializable minimal room data (inside reservations)

    :param room: A `Room`
    """
    data = room.to_serializable('__api_minimal_public__')
    data['_type'] = 'Room'
    return data


def _serializable_reservation(reservation_data, include_room=False):
    """Serializable reservation (standalone or inside room)

    :param reservation_data: Reservation data
    :param include_room: Include minimal room information
    """
    reservation = reservation_data['reservation']
    data = reservation.to_serializable('__api_public__', converters={datetime: _add_server_tz})
    data['_type'] = 'Reservation'
    data['repeatability'] = None
    if reservation.repeat_frequency:
        data['repeatability'] = RepeatMapping.get_short_name(*reservation.repetition)
    data['vcList'] = reservation_data['vc_equipment']
    if include_room:
        data['room'] = _serializable_room_minimal(reservation_data['reservation'].room)
    if 'occurrences' in reservation_data:
        data['occurrences'] = [o.to_serializable('__api_public__', converters={datetime: _add_server_tz})
                               for o in reservation_data['occurrences']]
    return data


def _ical_serialize_repeatability(data):
    start_dt_utc = data['startDT'].astimezone(pytz.utc)
    end_dt_utc = data['endDT'].astimezone(pytz.utc)
    WEEK_DAYS = 'MO TU WE TH FR SA SU'.split()
    recur = ical.vRecur()
    recur['until'] = end_dt_utc
    if data['repeat_frequency'] == RepeatFrequency.DAY:
        recur['freq'] = 'daily'
    elif data['repeat_frequency'] == RepeatFrequency.WEEK:
        recur['freq'] = 'weekly'
        recur['interval'] = data['repeat_interval']
    elif data['repeat_frequency'] == RepeatFrequency.MONTH:
        recur['freq'] = 'monthly'
        recur['byday'] = '{}{}'.format(start_dt_utc.day // 7, WEEK_DAYS[start_dt_utc.weekday()])
    return recur


def _ical_serialize_reservation(cal, data, now):
    start_dt_utc = data['startDT'].astimezone(pytz.utc)
    end_dt_utc = datetime.combine(data['startDT'].date(), data['endDT'].timetz()).astimezone(pytz.utc)

    event = icalendar.Event()
    event.add('uid', 'indico-resv-%s@cern.ch' % data['id'])
    event.add('dtstamp', now)
    event.add('dtstart', start_dt_utc)
    event.add('dtend', end_dt_utc)
    event.add('url', data['bookingUrl'])
    event.add('summary', data['reason'])
    event.add('location', u'{}: {}'.format(data['location'], data['room']['fullName']))
    event.add('description', data['reason'].decode('utf-8') + '\n\n' + data['bookingUrl'])
    if data['repeat_frequency'] != RepeatFrequency.NEVER:
        event.add('rrule', _ical_serialize_repeatability(data))
    cal.add_component(event)


def _add_server_tz(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=get_timezone(Config.getInstance().getDefaultTimezone()))
    return dt


def _yesno(value):
    return value.lower() in {'yes', 'y', '1', 'true'}


def _get_reservation_state_filter(params):
    cancelled = get_query_parameter(params, ['cxl', 'cancelled'])
    rejected = get_query_parameter(params, ['rej', 'rejected'])
    confirmed = get_query_parameter(params, ['confirmed'])
    archived = get_query_parameter(params, ['arch', 'archived', 'archival'])
    repeating = get_query_parameter(params, ['rec', 'recurring', 'rep', 'repeating'])
    avc = get_query_parameter(params, ['avc'])
    avc_support = get_query_parameter(params, ['avcs', 'avcsupport'])
    startup_support = get_query_parameter(params, ['sts', 'startupsupport'])
    booked_for = get_query_parameter(params, ['bf', 'bookedfor'])

    filters = []
    if cancelled is not None:
        filters.append(Reservation.is_cancelled == _yesno(cancelled))
    if rejected is not None:
        filters.append(Reservation.is_rejected == _yesno(rejected))
    if confirmed is not None:
        if confirmed == 'pending':
            filters.append(Reservation.is_pending)
        elif _yesno(confirmed):
            filters.append(Reservation.is_accepted)
        else:
            filters.append(~Reservation.is_accepted)
            filters.append(Reservation.is_rejected | Reservation.is_cancelled)
    if archived is not None:
        filters.append(Reservation.is_archived == _yesno(archived))
    if repeating is not None:
        if _yesno(repeating):
            filters.append(Reservation.repeat_frequency != 0)
        else:
            filters.append(Reservation.repeat_frequency == 0)
    if avc is not None:
        filters.append(Reservation.uses_vc == _yesno(avc))
    if avc_support is not None:
        filters.append(Reservation.needs_vc_assistance == _yesno(avc_support))
    if startup_support is not None:
        filters.append(Reservation.needs_assistance == _yesno(startup_support))
    if booked_for:
        like_str = '%{}%'.format(booked_for.replace('?', '_').replace('*', '%'))
        filters.append(Reservation.booked_for_name.ilike(like_str))
    return filters
