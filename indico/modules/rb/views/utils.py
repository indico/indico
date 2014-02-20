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

from calendar import day_name
from datetime import time

from MaKaC.webinterface import urlHandlers as UH

from ..models.utils import Serializer


class Bar(Serializer):
    __public__ = [
        'forReservation', 'startDT', 'endDT', ('kind', 'type'), 'blocking'
    ]

    BLOCKED, PREBOOKED, PRECONCURRENT, UNAVAILABLE, CANDIDATE, PRECONFLICT, CONFLICT = range(7)
    # BLOCKED:        room is blocked (dark-gray)
    # CANDIDATE:      represents new reservation (green)
    # CONFLICT:       overlap between candidate and confirmed resv. (dark red)
    # PREBOOKED:      represents pre-reservation (yellow)
    # PRECONFLICT:    represents conflict with pre-reservation (dark blue)
    # PRECONCURRENT:  conflicting pre-reservations (light blue)
    # UNAVAILABLE :   represents confirmed reservation (orange)

    def __init__(self, date, start_time, end_time, kind,
                 reservation_id, reservation_reason,
                 reservation_booked_for_name, reservation_location_name,
                 blocking):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time

        self.reservation_id = reservation_id
        self.booked_for_name = reservation_booked_for_name
        self.reservation_reason = reservation_reason
        self.reservation_location = reservation_location_name

        self.kind = kind
        self.blocking = blocking

    def __cmp__(self, other):
        return cmp(self.kind, other.kind)

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

    def get_time(self, attr):
        return {
            'date': self.date,
            'tz': None,
            'time': time.strftime(getattr(self, attr), '%H:%M')
        }

    @property
    def forReservation(self):
        return {
            'id': self.reservation_id,
            'bookedForName': self.booked_for_name,
            'reason': self.reservation_reason,
            'bookingUrl': UH.UHRoomBookingBookingDetails.getURL(
                roomLocation=self.reservation_location,
                resvID=self.reservation_id
            ) if self.reservation_id else None
        }

    @property
    def startDT(self):
        return self.get_time('start_time')

    @property
    def endDT(self):
        return self.get_time('end_time')


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


def barsList2Dictionary(bars):
    """
    Converts:
    list of bars => dictionary of bars, key = datetime, value = list of bars
    """
    h = {}
    for bar in bars:
        d = bar.start_date.date()
        if h.has_key(d):
            h[d].append(bar)
        else:
            h[d] = [bar]
    return h


def addOverlappingPrebookings(bars):
    """
    Adds bars representing overlapping pre-bookings.
    Returns new bars dictionary.
    """

    # For each day
    for dt in bars.keys():
        dayBars = bars[dt]

        # For each (prebooked) bar i
        for i in xrange(0, len(dayBars)):
            bar = dayBars[i]
            if bar.type == Bar.PREBOOKED:

                # For each (prebooked) bar j
                for j in xrange(i+1, len(dayBars)):
                    collCand = dayBars[j]
                    if collCand.type == Bar.PREBOOKED:

                        # If there is an overlap, add PRECONCURRENT bar
                        over = overlap(bar.startDT, bar.endDT, collCand.startDT, collCand.endDT)
                        if (over and bar.forReservation.room == collCand.forReservation.room and
                            collCand.forReservation != bar.forReservation):
                            collision = Collision(over, collCand.forReservation)
                            dayBars.append(Bar(collision, Bar.PRECONCURRENT))

        bars[dt] = dayBars # With added concurrent prebooking bars

    return bars


def sortBarsByImportance(bars, calendarStartDT, calendarEndDT):
    """
    Moves conflict bars to the end of the list,
    so they will be drawn last and therefore be visible.

    Returns sorted bars.
    """
    for dt in bars.keys():
        dayBars = bars[dt]
        dayBars.sort()
        bars[dt] = dayBars

    for day in iterdays(calendarStartDT, calendarEndDT):
        if not bars.has_key(day.date()):
           bars[day.date()] = []

    return bars


def getRoomBarsList(rooms):
    roomBarsList = []
    if rooms is None:
        rooms = []
    for room in rooms:
        roomBarsList.append(RoomBars(room, []))
    roomBarsList.sort()
    return roomBarsList


def introduceRooms(rooms, dayBarsDic, calendarStartDT, calendarEndDT,
                   showEmptyDays=True, showEmptyRooms=True, user=None):
    # Input:
    # dayBarsDic is a dictionary date => [bar1, bar2, bar3, ...]
    #
    # Output:
    # newDayBarsDic is a dictionary date => [roomBars1, roomBars2, roomBars3, ...],
    # where roomBars is object JSON:{ room: RoomBase, bars: [bar1, bar2, bar3, ...] }
    #import copy
    #cleanRoomBarsList = getRoomBarsList(rooms)
    newDayBarsDic = {}
    from MaKaC.common.utils import formatDate
    for day in iterdays(calendarStartDT, calendarEndDT):
        dayBars = dayBarsDic[day.date()]
        roomBarsDic = {}
        for bar in dayBars:
           # bar.canReject = False
           # bar.canReject = bar.forReservation.id is not None and bar.forReservation.canReject(user)
           # if bar.forReservation.repeatability != None:
           #     bar.rejectURL = str(urlHandlers.UHRoomBookingRejectBookingOccurrence
           #                                    .getURL(bar.forReservation, formatDate(bar.startDT.date())))
           # else:
           #     bar.rejectURL = str(urlHandlers.UHRoomBookingRejectBooking.getURL(bar.forReservation))
            room = bar.forReservation.room
            if not roomBarsDic.has_key(room):
                roomBarsDic[room] = []
            # Bars order should be preserved
            roomBarsDic[room].append(bar)

        if showEmptyRooms:
            dayRoomBarsList = getRoomBarsList(rooms)  # copy.copy(cleanRoomBarsList)

            for roomBar in dayRoomBarsList:
                roomBar.bars = roomBarsDic.get(roomBar.room, [])
        else:
            dayRoomBarsList = []
            for room in roomBarsDic.keys():
                dayRoomBarsList.append(RoomBars(room,roomBarsDic[room]))

        if showEmptyDays or len(dayBars) > 0:
            newDayBarsDic[day.date()] = dayRoomBarsList

    return newDayBarsDic


def getDayAttrsForRoom(dayDT, room):
    attrs = {'tooltip': '', 'className': ''}
    roomBlocked = room.getBlockedDay(dayDT)
    if roomBlocked:
        block = roomBlocked.block
    if roomBlocked and block.canOverride(ContextManager.get('currentUser'), explicitOnly=True):
        attrs['className'] = "blocked_permitted"
        attrs['tooltip'] = _('Blocked by %s:\n%s\n\n<b>You are permitted to '
                             'override the blocking.</b>') % (block.createdByUser.getFullName(), block.message)
    elif roomBlocked and roomBlocked.active is True:
        if block.canOverride(ContextManager.get('currentUser'), room):
            attrs['className'] = "blocked_override"
            attrs['tooltip'] = _('Blocked by %s:\n%s\n\n<b>You own this room or are an administrator '
                                 'and are thus permitted to override the blocking. Please use this '
                                 'privilege with care!</b>') % (block.createdByUser.getFullName(), block.message)
        else:
            attrs['className'] = "blocked"
            attrs['tooltip'] = _('Blocked by %s:\n%s') % (block.createdByUser.getFullName(), block.message)
    elif roomBlocked and roomBlocked.active is None:
        attrs['className'] = "preblocked"
        attrs['tooltip'] = _('Blocking requested by %s:\n%s\n\n'
                             '<b>If this blocking is approved, any colliding bookings will be rejected!</b>'
                             ) % (block.createdByUser.getFullName(), block.message)
    return attrs


def makePercentageString(val):
    """ Converts a float in [0, 1] to a percentage string
        ex:
            0.626333 -> 63%
            0.623333 -> 62%
    """
    assert 0 <= val <= 1
    return '{}%'.format(int(round(val * 100)))
