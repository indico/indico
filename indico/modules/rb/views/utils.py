# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from indico.modules.rb.models.utils import Serializer
from indico.util.date_time import format_time
from MaKaC.webinterface import urlHandlers as UH


class Bar(Serializer):
    __public__ = [
        'forReservation', 'startDT', 'endDT', ('kind', 'type'), 'blocking'
    ]

    BLOCKED, PREBOOKED, PRECONCURRENT, UNAVAILABLE, CANDIDATE, PRECONFLICT, CONFLICT = range(7)
    _mapping = {
        BLOCKED: 'blocked',                 # A blocked-room period
        CANDIDATE: 'candidate',             # A reservation candidate
        CONFLICT: 'conflict',               # A conflicting reservation candidate
        PREBOOKED: 'pre-booked',            # A unconfirmed reservation
        PRECONCURRENT: 'pre-concurrent',    # A conflict between unconfirmed reservations
        PRECONFLICT: 'pre-conflict',        # A conflicting unconfirmed reservation
        UNAVAILABLE: 'unavailable'          # A confirmed reservation
    }

    def __init__(self, start, end, kind=CANDIDATE, reservation=None, overlapping=False, blocking=None):
        self.start = start
        self.end = end
        self.reservation = reservation

        if reservation is not None:
            if not overlapping:
                kind = Bar.UNAVAILABLE if reservation.is_confirmed else Bar.PREBOOKED
            else:
                kind = Bar.CONFLICT if reservation.is_confirmed else Bar.PRECONFLICT

        self.kind = kind
        self.blocking = blocking

    def __cmp__(self, other):
        return cmp(self.kind, other.kind)

    def __repr__(self):
        return '<Bar({0}, {1}, {2}, {3}, {4})>'.format(
            self.start.date(),
            self.start.strftime('%H:%M'),
            self.end.strftime('%H:%M'),
            self.reservation.id,
            self._mapping[self.kind]
        )

    @classmethod
    def from_occurrence(cls, occurrence):
        return cls(
            start=occurrence.start,
            end=occurrence.end,
            reservation=occurrence.reservation)

    @staticmethod
    def get_kind(rid, is_confirmed):
        if rid:
            return Bar.UNAVAILABLE if is_confirmed else Bar.PREBOOKED
        else:
            return Bar.CANDIDATE

    @staticmethod
    def get_mutual_kind(rid1, is_confirmed1, rid2, is_confirmed2):
        if is_confirmed1:
            return Bar.CONFLICT
        else:
            if not rid2:
                return Bar.PRECONFLICT
            elif is_confirmed2:
                return Bar.CONFLICT
            else:
                return Bar.PRECONCURRENT

    @property
    def date(self):
        return self.start.date()

    @property
    def forReservation(self):
        if not self.reservation:
            return None
        else:
            return {
                'id': self.reservation.id,
                'bookedForName': self.reservation.booked_for_name,
                'reason': self.reservation.booking_reason,
                'bookingUrl': str(UH.UHRoomBookingBookingDetails.getURL(
                    roomLocation=self.reservation.room.location.name,
                    resvID=self.reservation.id
                ))
            }

    @property
    def importance(self):
        return self.kind

    @property
    def startDT(self):
        return self.get_datetime('start')

    @property
    def endDT(self):
        return self.get_datetime('end')

    def get_datetime(self, attr):
        return {
            'date': str(self.start.date()),
            'tz': None,
            'time': format_time(getattr(self, attr))
        }


class BlockingDetailsForBars(Serializer):
    __public__ = ['id', 'message', 'creator']

    def __init__(self, bid, message, creator_id):
        self.id = bid
        self.message = message
        self.creator_id = creator_id

    @property
    def creator(self):
        return self.creator_id


class RoomDetailsForBars(Serializer):
    __public__ = [
        'building', 'name', 'floor',
        ('number', 'roomNr'), ('location_name', 'locationName'),
        'id', ('kind', 'type'), ('booking_url', 'bookingUrl')
    ]

    def __init__(self, room, location_name):
        self.room = room
        self.location_name = location_name

    def __getattr__(self, attr):
        return getattr(self.room, attr)


class DayBar(Serializer):
    __public__ = [('room_details', 'room'), 'bars']

    def __init__(self, room_details, bars=None):
        self.room_details = room_details
        self.bars = bars or []

    def addBar(self, bar):
        self.bars.append(bar)

    def __cmp__(self, other):
        return cmp(self.room_details, other.room_details)


def updateOldDateStyle(d):
    for t in ['e', 's']:
        dt = d['start_date' if t == 's' else 'end_date']
        for p in ['Day', 'Month', 'Year']:
            d[t + p] = getattr(dt, p.lower())


def getNewDictOnlyWith(d, keys=[], **kw):
    for k in keys:
        if k in d:
            kw[k] = d[k]
    return kw


def makePercentageString(val):
    """ Converts a float in [0, 1] to a percentage string
        ex:
            0.626333 -> 63%
            0.623333 -> 62%
    """
    assert 0 <= val <= 1
    return '{0:.02f}%'.format(val * 100)
