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

from MaKaC.rb_reservation import ReservationBase, Collision, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.plugins.RoomBooking.default.room import Room
from MaKaC.rb_tools import iterdays
from calendar import day_name
from MaKaC.rb_location import Location, CrossLocationFactory
from indico.util.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.roomBooking import IRoomBarFossil, IBarFossil


class Bar( Fossilizable ):
    """
    Keeps data necessary for graphical bar on calendar.
    """
    fossilizes(IBarFossil)
    PREBOOKED, PRECONCURRENT, UNAVAILABLE, CANDIDATE, PRECONFLICT, CONFLICT = xrange( 0, 6 )
    # I know this names are not wisely choosed; it's due to unexpected additions
    # without refactoring
    # UNAVAILABLE :   represents confirmed reservation (bright-red)
    # CANDIDATE:      represents new reservation (green)
    # CONFLICT:       overlap between candidate and confirmed resv. (dark red)
    # PREBOOKED:      represents pre-reservation (yellow)
    # PRECONFLICT:    represents conflict with pre-reservation (orange)
    # PRECONCURRENT:  conflicting pre-reservations

    def __init__( self, c, barType ):
        self.startDT = c.startDT
        self.endDT = c.endDT
        self.forReservation = c.withReservation
        self.type = barType

    def __cmp__( self, obj ):
        return cmp( self.type, obj.type )


class RoomBars( Fossilizable ):

    fossilizes(IRoomBarFossil)

    room = None
    bars = []

    def __init__( self, room, bars ):
        self.room = room
        self.bars = bars
    def __cmp__( self, obj ):
        return cmp( self.room, obj.room )


# 3. Details of...

def barsList2Dictionary( bars ):
    """
    Converts:
    list of bars => dictionary of bars, key = datetime, value = list of bars
    """
    h = {}
    for bar in bars:
        d = bar.startDT.date()
        if h.has_key( d ):
            h[d].append( bar )
        else:
            h[d] = [bar]
    return h

def addOverlappingPrebookings( bars ):
    """
    Adds bars representing overlapping pre-bookings.
    Returns new bars dictionary.
    """

    # For each day
    for dt in bars.keys():
        dayBars = bars[dt]

        # For each (prebooked) bar i
        for i in xrange( 0, len( dayBars ) ):
            bar = dayBars[i]
            if bar.type == Bar.PREBOOKED:

                # For each (prebooked) bar j
                for j in xrange( i+1, len( dayBars ) ):
                    collCand = dayBars[j]
                    if collCand.type == Bar.PREBOOKED:

                        # If there is an overlap, add PRECONCURRENT bar
                        over = overlap( bar.startDT, bar.endDT, collCand.startDT, collCand.endDT )
                        if over and bar.forReservation.room == collCand.forReservation.room and collCand.forReservation != bar.forReservation:
                            collision = Collision( over, collCand.forReservation )
                            dayBars.append( Bar( collision, Bar.PRECONCURRENT ) )

        bars[dt] = dayBars # With added concurrent prebooking bars

    return bars

def sortBarsByImportance( bars, calendarStartDT, calendarEndDT ):
    """
    Moves conflict bars to the end of the list,
    so they will be drawn last and therefore be visible.

    Returns sorted bars.
    """
    for dt in bars.keys():
        dayBars = bars[dt]
        dayBars.sort()
        bars[dt] = dayBars

    for day in iterdays( calendarStartDT, calendarEndDT ):
        if not bars.has_key( day.date() ):
           bars[day.date()] = []

    return bars

def getRoomBarsList( rooms ):
    roomBarsList = []
    if rooms is None:
        rooms=[]
    for room in rooms:
        roomBarsList.append( RoomBars( room, [] ) )
    roomBarsList.sort()
    return roomBarsList

def introduceRooms( rooms, dayBarsDic, calendarStartDT, calendarEndDT, showEmptyDays=True, showEmptyRooms=True, user = None ):
    # Input:
    # dayBarsDic is a dictionary date => [bar1, bar2, bar3, ...]
    #
    # Output:
    # newDayBarsDic is a dictionary date => [roomBars1, roomBars2, roomBars3, ...],
    # where roomBars is object JSON:{ room: RoomBase, bars: [bar1, bar2, bar3, ...] }
    #import copy
    #cleanRoomBarsList = getRoomBarsList( rooms )
    newDayBarsDic = {}
    from MaKaC.common.utils import formatDate
    for day in iterdays( calendarStartDT, calendarEndDT ):
        dayBars = dayBarsDic[day.date()]
        roomBarsDic = {}
        for bar in dayBars:
#            bar.canReject = False
#            bar.canReject = bar.forReservation.id is not None and bar.forReservation.canReject(user)
#            if bar.forReservation.repeatability != None:
#                bar.rejectURL = str(urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL( bar.forReservation, formatDate(bar.startDT.date()) ))
#            else:
#                bar.rejectURL = str(urlHandlers.UHRoomBookingRejectBooking.getURL( bar.forReservation ))
            room = bar.forReservation.room
            if not roomBarsDic.has_key( room ):
                roomBarsDic[room] = []
            # Bars order should be preserved
            roomBarsDic[room].append( bar )

        if showEmptyRooms:
            dayRoomBarsList = getRoomBarsList( rooms ) #copy.copy( cleanRoomBarsList )

            for roomBar in dayRoomBarsList:
                roomBar.bars = roomBarsDic.get( roomBar.room, [] )
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
        attrs['tooltip'] = _('Blocked by %s:\n%s\n\n<b>You are permitted to override the blocking.</b>') % (block.createdByUser.getFullName(), block.message)
    elif roomBlocked and roomBlocked.active is True:
        if block.canOverride(ContextManager.get('currentUser'), room):
            attrs['className'] = "blocked_override"
            attrs['tooltip'] = _('Blocked by %s:\n%s\n\n<b>You own this room or are an administrator and are thus permitted to override the blocking. Please use this privilege with care!</b>') % (block.createdByUser.getFullName(), block.message)
        else:
            attrs['className'] = "blocked"
            attrs['tooltip'] = _('Blocked by %s:\n%s') % (block.createdByUser.getFullName(), block.message)
    elif roomBlocked and roomBlocked.active is None:
        attrs['className'] = "preblocked"
        attrs['tooltip'] = _('Blocking requested by %s:\n%s\n\n<b>If this blocking is approved, any colliding bookings will be rejected!</b>') % (block.createdByUser.getFullName(), block.message)
    return attrs
