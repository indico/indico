# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import MaKaC.webinterface.rh.roomBooking as roomBooking


def index( req, **params ):
    return roomBooking.RHRoomBookingWelcome( req ).process( params )

# 1. Searching
def search4Rooms( req, **params ):
    return roomBooking.RHRoomBookingSearch4Rooms( req ).process( params )
def search4Bookings( req, **params ):
    return roomBooking.RHRoomBookingSearch4Bookings( req ).process( params )
def search4Users( req, **params ):
    return roomBooking.RHRoomBookingSearch4Users( req ).process( params )

# 2. List of...
def roomList( req, **params ):
    return roomBooking.RHRoomBookingRoomList( req ).process( params )
def bookingList( req, **params ):
    r = roomBooking.RHRoomBookingBookingList(req).process(params)
    return r

# 3. Details of...
def roomDetails( req, **params ):
    return roomBooking.RHRoomBookingRoomDetails( req ).process( params )
def roomStats( req, **params ):
    return roomBooking.RHRoomBookingRoomStats( req ).process( params )
def bookingDetails( req, **params ):
    return roomBooking.RHRoomBookingBookingDetails(req).process(params)

# 4. Forms for creation AND modification
def bookingForm( req, **params ):
    return roomBooking.RHRoomBookingBookingForm(req).process(params)
def roomForm( req, **params ):
    return roomBooking.RHRoomBookingRoomForm(req).process(params)
def cloneBooking( req, **params ):
    return roomBooking.RHRoomBookingCloneBooking(req).process(params)

# 4. Physical INSERT or UPDATE
def saveBooking( req, **params ):
    return roomBooking.RHRoomBookingSaveBooking(req).process(params)
def saveRoom( req, **params ):
    return roomBooking.RHRoomBookingSaveRoom(req).process(params)

def deleteRoom( req, **params ):
    return roomBooking.RHRoomBookingDeleteRoom(req).process(params)
def deleteBooking( req, **params ):
    return roomBooking.RHRoomBookingDeleteBooking(req).process(params)
def cancelBooking( req, **params ):
    return roomBooking.RHRoomBookingCancelBooking(req).process(params)
def cancelBookingOccurrence( req, **params ):
    return roomBooking.RHRoomBookingCancelBookingOccurrence(req).process(params)
def acceptBooking( req, **params ):
    return roomBooking.RHRoomBookingAcceptBooking(req).process(params)
def rejectBooking( req, **params ):
    return roomBooking.RHRoomBookingRejectBooking(req).process(params)
def rejectBookingOccurrence( req, **params ):
    return roomBooking.RHRoomBookingRejectBookingOccurrence(req).process(params)
def rejectAllConflicting( req, **params ):
    return roomBooking.RHRoomBookingRejectALlConflicting(req).process(params)

def statement( req, **params ):
    return roomBooking.RHRoomBookingStatement(req).process(params)
def admin( req, **params ):
    return roomBooking.RHRoomBookingAdmin(req).process(params)
def adminLocation( req, **params ):
    return roomBooking.RHRoomBookingAdminLocation(req).process(params)
def setDefaultLocation( req, **params ):
    return roomBooking.RHRoomBookingSetDefaultLocation(req).process(params)
def saveLocation( req, **params ):
    return roomBooking.RHRoomBookingSaveLocation(req).process(params)
def deleteLocation( req, **params ):
    return roomBooking.RHRoomBookingDeleteLocation(req).process(params)
def saveEquipment( req, **params ):
    return roomBooking.RHRoomBookingSaveEquipment(req).process(params)
def deleteEquipment( req, **params ):
    return roomBooking.RHRoomBookingDeleteEquipment(req).process(params)

def saveCustomAttributes( req, **params ):
    return roomBooking.RHRoomBookingSaveCustomAttribute(req).process(params)

def deleteCustomAttribute( req, **params ):
    return roomBooking.RHRoomBookingDeleteCustomAttribute(req).process(params)

#    import wingdbstub
#    if wingdbstub.debugger != None:
#        wingdbstub.debugger.StartDebug()

def sendRoomPhoto( req, **params ):
    return roomBooking.RHRoomBookingSendRoomPhoto(req).process(params)

# AJAX: Returns "Warning: non-working day (weekend or holidays)"
def getDateWarning( req, **params ):
    return roomBooking.RHRoomBookingGetDateWarning(req).process(params)

# AJAX: Returns <select></select> list of rooms
def getRoomSelectList( req, **params ):
    return roomBooking.RHRoomBookingGetRoomSelectList(req).process(params)

# AJAX: Returns <select></select> list of rooms
def getRoomSelectList4SubEvents( req, **params ):
    params['forSubEvents'] = 'True'
    return roomBooking.RHRoomBookingGetRoomSelectList(req).process(params)

