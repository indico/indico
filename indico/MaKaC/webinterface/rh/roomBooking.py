# -*- coding: utf-8 -*-
##
## $Id: roomBooking.py,v 1.19 2009/06/02 14:33:23 jose Exp $
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

# Most of the following imports are probably not necessary - to clean

import os

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.locators as locators
from MaKaC.common.general import *
from MaKaC.common.Configuration import Config
from MaKaC.webinterface.rh.base import RHProtected, RoomBookingDBMixin
from datetime import datetime, timedelta
from MaKaC.common.utils import HolidaysHolder
from MaKaC.common.datetimeParser import parse_date

# The following are room booking related

import MaKaC.webinterface.pages.roomBooking as roomBooking_wp
import MaKaC.webinterface.pages.admins as admins
from MaKaC.rb_room import RoomBase
from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.rb_location import CrossLocationQueries, RoomGUID, Location
from MaKaC.rb_tools import intd, FormMode
from MaKaC import plugins
from MaKaC.errors import MaKaCError

class CandidateDataFrom( object ):
    DEFAULTS, PARAMS, SESSION = xrange( 3 )

# 0. Base classes


class RHRoomBookingBase( RoomBookingDBMixin, RHProtected ):
    """
    All room booking related hanlders are derived from this class.
    This gives them:
    - several general use methods
    - login-protection
    - auto connecting/disconnecting from room booking db
    """

    def _checkProtection( self ):
        RHProtected._checkProtection(self)

    def _clearSessionState( self ):
        session = self._websession

        session.setVar( "actionSucceeded", None )
        session.setVar( "deletionFailed", None )
        session.setVar( "formMode", None )

        session.setVar( "candDataInSession", None )
        session.setVar( "candDataInParams", None )
        session.setVar( "afterCalPreview", None )

        session.setVar( "showErrors", False )
        session.setVar( "errors", None )
        session.setVar( "thereAreConflicts", None )

        session.setVar( "roomID", None )
        session.setVar( "roomLocation", None )
        session.setVar( "resvID", None )

    def _checkParamsRepeatingPeriod( self, params ):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """
        sDay = params.get( "sDay" )
        if sDay and len( sDay.strip() ) > 0:
            sDay = int( sDay.strip() )

        eDay = params.get( "eDay" )
        if eDay and len( eDay.strip() ) > 0:
            eDay = int( eDay.strip() )

        sMonth = params.get( "sMonth" )
        if sMonth and len( sMonth.strip() ) > 0:
            sMonth = int( sMonth.strip() )

        eMonth = params.get( "eMonth" )
        if eMonth and len( eMonth.strip() ) > 0:
            eMonth = int( eMonth.strip() )

        sYear = params.get( "sYear" )
        if sYear and len( sYear.strip() ) > 0:
            sYear = int( sYear.strip() )

        eYear = params.get( "eYear" )
        if eYear and len( eYear.strip() ) > 0:
            eYear = int( eYear.strip() )


        sTime = params.get( "sTime" )
        if sTime and len( sTime.strip() ) > 0:
            sTime = sTime.strip()
        eTime = params.get( "eTime" )
        if eTime and len( eTime.strip() ) > 0:
            eTime = eTime.strip()

        # process sTime and eTime
        if sTime and eTime:
            t = sTime.split( ':' )
            sHour = int( t[0] )
            sMinute = int( t[1] )
            t = eTime.split( ':' )
            eHour = int( t[0] )
            eMinute = int( t[1] )

        repeatability = params.get( "repeatability" )
        if repeatability and len( repeatability.strip() ) > 0:
            if repeatability == "None":
                repeatability = None
            else:
                repeatability = int( repeatability.strip() )

        self._startDT = None
        self._endDT = None
        self._repeatability = repeatability
        if sYear and sMonth and sDay and sTime and eYear and eMonth and eDay and eTime:
            # Full period specified
            self._startDT = datetime( sYear, sMonth, sDay, sHour, sMinute )
            self._endDT = datetime( eYear, eMonth, eDay, eHour, eMinute )
        elif sYear and sMonth and sDay and eYear and eMonth and eDay:
            # There are no times
            self._startDT = datetime( sYear, sMonth, sDay, 0, 0, 0 )
            self._endDT = datetime( eYear, eMonth, eDay, 23, 59, 59 )
        elif sTime and eTime:
            # There are no dates
            self._startDT = datetime( 1990, 1, 1, sHour, sMinute )
            self._endDT = datetime( 2030, 12, 31, eHour, eMinute )
        self._today=False
        if params.get( "day", "" ) == "today":
            self._today=True
            self._startDT = datetime.today().replace(hour=0,minute=0,second=0)
            self._endDT = self._startDT.replace(hour=23,minute=59,second=59)
    # Room

    def _saveRoomCandidateToSession( self, c ):
        session = self._websession     # Just an alias
        if self._formMode == FormMode.MODIF:
            session.setVar( "roomID", c.id )
            session.setVar( "roomLocation", c.locationName )

        session.setVar( "name", c.name )
        session.setVar( "site", c.site )
        session.setVar( "building", c.building )
        session.setVar( "floor", c.floor )
        session.setVar( "roomNr", c.roomNr )

        session.setVar( "isActive", c.isActive )
        session.setVar( "isReservable", c.isReservable )
        session.setVar( "resvsNeedConfirmation", c.resvsNeedConfirmation )

        session.setVar( "responsibleId", c.responsibleId )
        session.setVar( "whereIsKey", c.whereIsKey )
        session.setVar( "telephone", c.telephone )

        session.setVar( "capacity", c.capacity )
        session.setVar( "division", c.division )
        session.setVar( "surfaceArea", c.surfaceArea )
        session.setVar( "comments", c.comments )

        session.setVar( "equipment", c.getEquipment() )
        for name, value in c.customAtts.iteritems():
            session.setVar( "cattr_" + name, value )

    def _getErrorsOfRoomCandidate( self, c ):
        errors = []
        #if not c.site:
        #    errors.append( "Site can not be blank" )
        if not c.floor:
            errors.append( "Floor can not be blank" )
        if not c.roomNr:
            errors.append( "Room number can not be blank" )
        if not c.responsibleId:
            errors.append( "Room must have a responsible person" )
        if not c.building or c.building < 1:
            errors.append( "Building must be a positive integer" )
        if not c.capacity or c.capacity < 1:
            errors.append( "Capacity must be a positive integer" )
        params = self._params
        if ( params['largePhotoPath'] != '' ) ^ ( params['smallPhotoPath'] != '' ):
            errors.append( "Either upload both photos or none")

        # Custom attributes
        manager = CrossLocationQueries.getCustomAttributesManager( c.locationName )
        for ca in manager.getAttributes( location = c.locationName ):
            if ca['required']:
                if not c.customAtts.has_key( ca['name'] ): # not exists
                    errors.append( ca['name'] + " can not be blank" )
                elif not c.customAtts[ ca['name'] ]:       # is empty
                    errors.append( ca['name'] + " can not be blank" )

        return errors

    def _loadRoomCandidateFromDefaults( self, candRoom ):
        candRoom.isActive = True

        candRoom.building = None
        candRoom.floor = ''
        candRoom.roomNr = ''

        candRoom.capacity = 20
        candRoom.site = ''
        candRoom.division = None
        candRoom.isReservable = True
        candRoom.resvsNeedConfirmation = False
        candRoom.photoId = None
        candRoom.externalId = None

        candRoom.telephone = ''      # str
        candRoom.surfaceArea = None
        candRoom.whereIsKey = ''
        candRoom.comments = ''
        candRoom.responsibleId = None

    def _loadRoomCandidateFromSession( self, candRoom ):
        session = self._websession # Just an alias

        candRoom.name = session.getVar( "name" )
        candRoom.site = session.getVar( "site" )
        candRoom.building = intd( session.getVar( "building" ) )
        candRoom.floor = session.getVar( "floor" )
        candRoom.roomNr = session.getVar( "roomNr" )

        candRoom.isActive = bool( session.getVar( "isActive" ) )
        candRoom.isReservable = bool( session.getVar( "isReservable" ) )
        candRoom.resvsNeedConfirmation = bool( session.getVar( "resvsNeedConfirmation" ) )

        candRoom.responsibleId = session.getVar( "responsibleId" )
        candRoom.whereIsKey = session.getVar( "whereIsKey" )
        candRoom.telephone = session.getVar( "telephone" )

        candRoom.capacity = intd( session.getVar( "capacity" ) )
        candRoom.division = session.getVar( "division" )
        candRoom.surfaceArea = intd( session.getVar( "surfaceArea" ) )
        candRoom.comments = session.getVar( "comments" )

        candRoom.setEquipment( session.getVar( "equipment" ) )

        manager = CrossLocationQueries.getCustomAttributesManager( candRoom.locationName )
        for ca in manager.getAttributes( location = candRoom.locationName ):
            value = session.getVar( "cattr_" + ca['name'] )
            if value != None:
                candRoom.customAtts[ ca['name'] ] = value


    def _loadRoomCandidateFromParams( self, candRoom, params ):
        candRoom.name = params.get( "name" )
        candRoom.site = params.get( "site" )
        candRoom.building = intd( params.get( "building" ) )
        candRoom.floor = params.get( "floor" )
        candRoom.roomNr = params.get( "roomNr" )

        candRoom.isActive = bool( params.get( "isActive" ) ) # Safe
        candRoom.isReservable = bool( params.get( "isReservable" ) ) # Safe
        candRoom.resvsNeedConfirmation = bool( params.get( "resvsNeedConfirmation" ) ) # Safe

        candRoom.responsibleId = params.get( "responsibleId" )
        if candRoom.responsibleId == "None":
            candRoom.responsibleId = None
        candRoom.whereIsKey = params.get( "whereIsKey" )
        candRoom.telephone = params.get( "telephone" )

        candRoom.capacity = intd( params.get( "capacity" ) )
        candRoom.division = params.get( "division" )
        candRoom.surfaceArea = intd( params.get( "surfaceArea" ) )
        candRoom.comments = params.get( "comments" )

        eqList = []
        vcList = []
        for k, v in params.iteritems():
            if k.startswith( "equ_" ) and v:
                eqList.append(k[4:len(k)])
            if k.startswith( "vc_" ) and v:
                vcList.append(k[3:])
        candRoom.setEquipment( eqList )
        candRoom.setAvailableVC(vcList)

        for k, v in params.iteritems():
            if k.startswith( "cattr_" ):
                attrName = k[6:len(k)]
                candRoom.customAtts[attrName] = v

    # Resv

    def _saveResvCandidateToSession( self, c ):
        session = self._websession
        if self._formMode == FormMode.MODIF:
            session.setVar( "resvID", c.id )
            session.setVar( "roomLocation", c.locationName )
        session.setVar( "roomID", c.room.id )
        session.setVar( "startDT", c.startDT )
        session.setVar( "endDT", c.endDT )
        session.setVar( "repeatability", c.repeatability )
        session.setVar( "bookedForName", c.bookedForName )
        session.setVar( "contactPhone", c.contactPhone )
        session.setVar( "contactEmail", c.contactEmail )
        session.setVar( "reason", c.reason )
        session.setVar( "usesAVC", c.usesAVC )
        session.setVar( "needsAVCSupport", c.needsAVCSupport )

        if hasattr(self, '_skipConflicting'):
            if self._skipConflicting:
                skip = 'on'
            else:
                skip = 'off'
            session.setVar( "skipConflicting", skip )

        if hasattr(c, "useVC"):
            session.setVar( "useVC",  c.useVC)


    def _getErrorsOfResvCandidate( self, c ):
        errors = []
        self._thereAreConflicts = False
        if not c.bookedForName:
            errors.append( "Booked for can not be blank" )
        if not c.reason:
            errors.append( "Purpose can not be blank" )
        if not c.isRejected and not c.isCancelled:
            collisions = c.getCollisions( sansID = self._candResv.id )
            if len( collisions ) > 0:
                if self._skipConflicting and c.startDT.date() != c.endDT.date():
                    for collision in collisions:
                        c.excludeDay( collision.startDT.date() )
                else:
                    self._thereAreConflicts = True
                    errors.append( "There are conflicts with other bookings" )

        return errors

    def _loadResvCandidateFromSession( self, candResv, params ):
        # After successful searching or failed save
        session = self._websession

        roomID = params['roomID']
        if isinstance( roomID, list ):
            roomID = int( roomID[0] )
        else:
            roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        if isinstance( roomLocation, list ):
            roomLocation = roomLocation[0]
        if not roomLocation:
            roomLocation = session.getVar( "roomLocation" )

        if not candResv:
            candResv = Location.parse( roomLocation ).factory.newReservation() # The same location as for room

        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        candResv.startDT = session.getVar( "startDT" )
        candResv.endDT = session.getVar( "endDT" )
        candResv.repeatability = session.getVar( "repeatability" )
        candResv.bookedForName = session.getVar( "bookedForName" )
        candResv.contactPhone = session.getVar( "contactPhone" )
        candResv.contactEmail = session.getVar( "contactEmail" )
        candResv.reason = session.getVar( "reason" )
        candResv.usesAVC = session.getVar( "usesAVC" )
        candResv.needsAVCSupport = session.getVar( "needsAVCSupport" )
        self._skipConflicting = session.getVar( "skipConflicting" ) == "on"

        useVC = session.getVar('useVC')
        if useVC is not None:
            candResv.useVC = useVC

        return candResv

    def _loadResvCandidateFromParams( self, candResv, params ):
        # After calendar preview
        roomID = params['roomID']
        if isinstance( roomID, list ):
            roomID = int( roomID[0] )
        else:
            roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        if isinstance( roomLocation, list ):
            roomLocation = roomLocation[0]
        if not candResv:
            candResv = Location.parse( roomLocation ).factory.newReservation() # The same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        self._checkParamsRepeatingPeriod( params )
        candResv.startDT = self._startDT
        candResv.endDT = self._endDT
        candResv.repeatability = self._repeatability
        candResv.bookedForName = params["bookedForName"]
        candResv.contactEmail = params["contactEmail"]
        candResv.contactPhone = params["contactPhone"]
        candResv.reason = params["reason"]
        candResv.usesAVC = params.get( "usesAVC" ) == "on"
        candResv.needsAVCSupport = params.get( "needsAVCSupport" ) == "on"
        self._skipConflicting = params.get( "skipConflicting" ) == "on"
        d = {}
        for vc in candResv.room.getAvailableVC():
            d[vc[:3]] = vc
        candResv.useVC = []
        for param in params:
            if len(param) > 3 and param[:3] == "vc_":
                vc = d.get(param[3:], None)
                if vc:
                    candResv.useVC.append(vc)
        return candResv

    def _loadResvCandidateFromDefaults( self, params ):
        ws = self._websession
        # After room details
        roomID = int( params['roomID'] )
        roomLocation = params['roomLocation']
        candResv = Location.parse( roomLocation ).factory.newReservation() # Create in the same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        # Generic defaults
        now = datetime.now()
        if now.weekday() in [4,5]:
            now = now + timedelta( 7 - now.weekday() )
        else:
            now = now + timedelta( 1 )
        if candResv.startDT == None:
            candResv.startDT = datetime( now.year, now.month, now.day, 8, 30 )
        if candResv.endDT == None:
            candResv.endDT = datetime( now.year, now.month, now.day, 17, 30 )
        if self._getUser():
            if candResv.bookedForName == None:
                candResv.bookedForName = self._getUser().getFullName()
            if candResv.contactEmail == None:
                candResv.contactEmail = self._getUser().getEmail()
            if candResv.contactPhone == None:
                candResv.contactPhone = self._getUser().getTelephone()
        else:
            candResv.bookedForName = candResv.contactEmail = candResv.contactPhone = ""
        if candResv.reason == None:
            candResv.reason = ""
        if candResv.usesAVC == None:
            candResv.usesAVC = False
        if candResv.needsAVCSupport == None:
            candResv.needsAVCSupport = False

        if not ws.getVar( "dontAssign" ):
            if ws.getVar( "defaultStartDT" ):
                candResv.startDT = ws.getVar( "defaultStartDT" )
            if ws.getVar( "defaultEndDT" ):
                candResv.endDT = ws.getVar( "defaultEndDT" )
            if ws.getVar( "defaultRepeatability" ) != None:
                candResv.repeatability = ws.getVar( "defaultRepeatability" )
            if ws.getVar( "defaultBookedForName" ):
                candResv.bookedForName = ws.getVar( "defaultBookedForName" )
            if ws.getVar( "defaultReason" ):
                candResv.reason = ws.getVar( "defaultReason" )

            if ws.getVar( "assign2Session" ):
                self._assign2Session = ws.getVar( "assign2Session" )
            if ws.getVar( "assign2Contribution" ):
                self._assign2Contributioon = ws.getVar( "assign2Contribution" )

        return candResv


class RHRoomBookingAdminBase( RHRoomBookingBase ):
    """
    Adds admin authorization. All classes that implement admin
    tasks should be derived from this class.
    """
    def _checkProtection( self ):
        if self._getUser() == None:
            self._checkSessionUser()
        elif not self._getUser().isAdmin():
            raise MaKaCError( "You are not authorized to take this action." )

class RHRoomBookingWelcome( RHRoomBookingBase ):
    _uh = urlHandlers.UHRoomBookingWelcome

    def _process( self ):
        #if self._getUser().isResponsibleForRooms():
        #    self._redirect( urlHandlers.UHRoomBookingBookingList.getURL( ofMyRooms = True, autoCriteria = True ) )
        #    return
        #self._redirect( urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True, autoCriteria = True ) )
        self._redirect( urlHandlers.UHRoomBookingSearch4Rooms.getURL( forNewBooking = True ))

# 1. Searching

class RHRoomBookingSearch4Rooms( RHRoomBookingBase ):

    def _cleanDefaultsFromSession( self ):
        websession = self._websession
        websession.setVar( "defaultStartDT", None )
        websession.setVar( "defaultEndDT", None )
        websession.setVar( "defaultRepeatability", None )
        websession.setVar( "defaultBookedForName", None )
        websession.setVar( "defaultReason", None )
        websession.setVar( "assign2Session", None )
        websession.setVar( "assign2Contribution", None )

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta( 7 - now.weekday() )

        websession = self._websession
        websession.setVar( "defaultStartDT", datetime( now.year, now.month, now.day, 8, 30 ) )
        websession.setVar( "defaultEndDT", datetime( now.year, now.month, now.day, 17, 30 ) )

    def _checkParams( self, params ):
        self._cleanDefaultsFromSession()
        self._setGeneralDefaultsInSession()
        self._forNewBooking = False
        self._eventRoomName = None
        if params.get( 'forNewBooking' ):
            self._forNewBooking = params.get( 'forNewBooking' ) == 'True'

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()
        self._equipment = CrossLocationQueries.getPossibleEquipment()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingSearch4Rooms( self, self._forNewBooking )
        return p.display()

class RHRoomBookingSearch4Bookings( RHRoomBookingBase ):

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingSearch4Bookings( self )
        return p.display()

class RHRoomBookingSearch4Users( RHRoomBookingBase ):

    def _checkParams( self, params ):

        roomID = params.get( "roomID" )
        roomLocation = params.get( "roomLocation" )
        candRoom = None
        if roomID:
            self._formMode = FormMode.MODIF
            roomID = int( roomID )
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        else:
            self._formMode = FormMode.NEW
            candRoom = Factory.newRoom()  # Is it OK? Potential bug.

        self._loadRoomCandidateFromParams( candRoom, params )
        self._saveRoomCandidateToSession( candRoom )

        # Set session
        self._websession.setVar( "showErrors", False )
        self._websession.setVar( "candDataInSession", True )

        if params.has_key( 'largePhotoPath' ): del params['largePhotoPath']
        if params.has_key( 'smallPhotoPath' ): del params['smallPhotoPath']

        self._forceWithoutExtAuth = True
        if params.has_key( 'searchExt' )  and  params['searchExt'] == 'Nice':
            self._forceWithoutExtAuth = False

    def _process( self ):
        p = roomBooking_wp.WPRoomBookingSearch4Users( self )
        return p.display( **self._getRequestParams() )

# 2. List of ...

class RHRoomBookingRoomList( RHRoomBookingBase ):

    def _checkParams( self, params ):

        self._roomLocation = None
        if params.get("roomLocation") and len( params["roomLocation"].strip() ) > 0:
            self._roomLocation = params["roomLocation"].strip()

        self._freeSearch = None
        if params.get("freeSearch") and len( params["freeSearch"].strip() ) > 0:
            s = params["freeSearch"].strip()
            # Remove commas
            self._freeSearch = ""
            for c in s:
                if c != ',': self._freeSearch += c

        self._capacity = None
        if params.get("capacity") and len( params["capacity"].strip() ) > 0:
            self._capacity = int( params["capacity"].strip() )

        self._availability = "Don't care"
        if params.get("availability") and len( params["availability"].strip() ) > 0:
            self._availability = params["availability"].strip()

        if self._availability != "Don't care":
            self._checkParamsRepeatingPeriod( params )

        self._includePrebookings = False
        if params.get( 'includePrebookings' ) == "on": self._includePrebookings = True

        # The end of "avail/don't care"

        # Equipment
        self._equipment = []
        for k, v in params.iteritems():
            if k[0:4] == "equ_" and v == "on":
                self._equipment.append( k[4:100] )

        # Special
        self._isReservable = self._ownedBy = self._isAutoConfirmed = None
        self._isActive = True

        if params.get( 'isReservable' ) == "on": self._isReservable = True
        if params.get( 'isAutoConfirmed' ) == "on": self._isAutoConfirmed = True

        # only admins can choose to consult non-active rooms
        if self._getUser() and self._getUser().isAdmin() and params.get( 'isActive', None ) != "on":
            self._isActive = None

        self._onlyMy = params.get( 'onlyMy' ) == "on"

    def _businessLogic( self ):
        if self._onlyMy: # Can't be done in checkParams since it must be after checkProtection
            self._title = "My rooms"
            self._ownedBy = self._getUser()

        r = RoomBase()
        r.capacity = self._capacity
        r.isActive = self._isActive
        #r.responsibleId = self._responsibleId
        r.isReservable = self._isReservable
        if self._isAutoConfirmed:
            r.resvsNeedConfirmation = False
        for eq in self._equipment:
            r.insertEquipment( eq )

        if self._availability == "Don't care":
            rooms = CrossLocationQueries.getRooms( location = self._roomLocation, freeText = self._freeSearch, ownedBy = self._ownedBy, roomExample = r )
            # Special care for capacity (20% => greater than)
            if len ( rooms ) == 0:
                rooms = CrossLocationQueries.getRooms( location = self._roomLocation, freeText = self._freeSearch, ownedBy = self._ownedBy, roomExample = r, minCapacity = True )
        else:
            # Period specification
            p = ReservationBase()
            p.startDT = self._startDT
            p.endDT = self._endDT
            p.repeatability = self._repeatability
            if self._includePrebookings:
                p.isConfirmed = None   # because it defaults to True

            # Set default values for later booking form
            self._websession.setVar( "defaultStartDT", p.startDT )
            self._websession.setVar( "defaultEndDT", p.endDT )
            self._websession.setVar( "defaultRepeatability", p.repeatability )

            available = ( self._availability == "Available" )

            rooms = CrossLocationQueries.getRooms( \
                location = self._roomLocation,
                freeText = self._freeSearch,
                ownedBy = self._ownedBy,
                roomExample = r,
                resvExample = p,
                available = available )
            # Special care for capacity (20% => greater than)
            if len ( rooms ) == 0:
                rooms = CrossLocationQueries.getRooms( \
                    location = self._roomLocation,
                    freeText = self._freeSearch,
                    ownedBy = self._ownedBy,
                    roomExample = r,
                    resvExample = p,
                    available = available,
                    minCapacity = True )

        rooms.sort()

        self._rooms = rooms

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomList( self, self._onlyMy )
        return p.display()

class RHRoomBookingBookingList( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self._roomGUIDs = []
        self._allRooms = False
        roomGUIDs = params.get( "roomGUID" )
        if isinstance( roomGUIDs, str ):
            if roomGUIDs == "allRooms":
                self._allRooms = True
                roomGUIDs = [ str(room.guid) for room in CrossLocationQueries.getRooms( allFast = True )]
            else:
                roomGUIDs = [roomGUIDs.strip()]
        if isinstance( roomGUIDs, list )  and  roomGUIDs != ['']:
            self._roomGUIDs = roomGUIDs

        resvEx = ReservationBase()
        self._checkParamsRepeatingPeriod( params )
        resvEx.startDT = self._startDT
        resvEx.endDT = self._endDT
        bookedForName = params.get( "bookedForName" )
        if bookedForName and len( bookedForName.strip() ) > 0:
            resvEx.bookedForName = bookedForName.strip()
        reason = params.get( "reason" )
        if reason and len( reason.strip() ) > 0:
            resvEx.reason = reason.strip()
        self._title = "Bookings"

        onlyPrebookings = params.get( "onlyPrebookings" )
        self._onlyPrebookings = False

        onlyBookings = params.get( "onlyBookings" )
        self._onlyBookings = False

        if onlyPrebookings and len( onlyPrebookings.strip() ) > 0:
            if onlyPrebookings == 'on':
                resvEx.isConfirmed = False
                self._title = "PRE-" + self._title
                self._onlyPrebookings = True
        elif onlyBookings and len( onlyBookings.strip() ) > 0:
            if onlyBookings == 'on':
                resvEx.isConfirmed = True
                self._onlyBookings = True
        else:
            # find pre-bookings as well
            resvEx.isConfirmed = None

        self._onlyMy = False
        onlyMy = params.get( "onlyMy" )
        if onlyMy and len( onlyMy.strip() ) > 0:
            if onlyMy == 'on':
                self._onlyMy = True
                self._title = "My " + self._title
        else:
            resvEx.createdBy = None
        self._ofMyRooms = False
        ofMyRooms = params.get( "ofMyRooms" )
        if ofMyRooms and len( ofMyRooms.strip() ) > 0:
            if ofMyRooms == 'on':
                self._ofMyRooms = True
                self._title = self._title + " for your rooms"
        else:
            self._rooms = None

        self._search = False
        search = params.get( "search" )
        if search and len( search.strip() ) > 0:
            if search == 'on':
                self._search = True
                self._title = "Search " + self._title

        self._order = params.get( "order", "" )

        isArchival = params.get( "isArchival" )
        if isArchival and len( isArchival.strip() ) > 0:
            self._isArchival = True
        else:
            self._isArchival = None

        self._autoCriteria = False
        if params.get( "autoCriteria" ) == "True" or not resvEx.startDT:
            now = datetime.now()
            after = now + timedelta( 30 ) # 1 month later

            resvEx.startDT = datetime( now.year, now.month, now.day, 0, 0, 0 )
            resvEx.endDT = datetime( after.year, after.month, after.day, 23, 59, 00 )
            self._autoCriteria = True
            self._isArchival = None

        isRejected = params.get( "isRejected" )
        if isRejected and len( isRejected.strip() ) > 0:
            resvEx.isRejected = isRejected == 'on'
        else:
            resvEx.isRejected = False
        isCancelled = params.get( "isCancelled" )
        if isCancelled and len( isCancelled.strip() ) > 0:
            resvEx.isCancelled = isCancelled == 'on'
        else:
            resvEx.isCancelled = False


        needsAVCSupport = params.get( "needsAVCSupport" )
        if needsAVCSupport and len( needsAVCSupport.strip() ) > 0:
            resvEx.needsAVCSupport = needsAVCSupport == 'on'
        else:
            resvEx.needsAVCSupport = None

        usesAVC = params.get( "usesAVC" )
        if usesAVC and len( usesAVC.strip() ) > 0:
            resvEx.usesAVC = usesAVC == 'on'
        else:
            resvEx.usesAVC = None

        isHeavy = params.get( "isHeavy" )
        if isHeavy and len( isHeavy.strip() ) > 0:
            self._isHeavy = True
        else:
            self._isHeavy = None

        self._resvEx = resvEx

        session = self._websession
        self._prebookingsRejected = session.getVar( 'prebookingsRejected' )
        self._subtitle = session.getVar( 'title' )
        self._description = session.getVar( 'description' )
        session.setVar( 'title', None )
        session.setVar( 'description', None )
        session.setVar( 'prebookingsRejected', None )


    def _process( self ):
        # The following can't be done in checkParams since it must be after checkProtection
        if self._onlyMy:
            self._resvEx.createdBy = str( self._getUser().id )
        if self._ofMyRooms:
            self._rooms = self._getUser().getRooms()
            self._roomGUIDs = None

        # Whether to show [Reject ALL conflicting PRE-bookings] button
        self._showRejectAllButton = False
        if self._rooms and not self._resvEx.isConfirmed:
            self._showRejectAllButton = True

        if self._roomGUIDs:
            rooms = [ RoomGUID.parse( rg ).getRoom() for rg in self._roomGUIDs ]
            if self._rooms is list:
                self._rooms.extend( rooms )
            else:
                self._rooms = rooms

        # Init
        resvEx = self._resvEx

        days = None
        self._overload = False
        if resvEx.startDT and resvEx.endDT:
            if ( resvEx.endDT - resvEx.startDT ).days > 400:
                self._overload = True
                self._resvs = []
            else:
                # Prepare 'days' so .getReservations will use days index
                if resvEx.repeatability == None:
                    resvEx.repeatability = RepeatabilityEnum.daily
                periods = resvEx.splitToPeriods()
                days = [ period.startDT.date() for period in periods ]
                if len( days ) > 32:
                    days = None # Using day index won't help

        if not self._overload:
            self._resvs = CrossLocationQueries.getReservations( resvExample = resvEx, rooms = self._rooms, archival = self._isArchival, heavy = self._isHeavy, days = days )


        p = roomBooking_wp.WPRoomBookingBookingList( self )
        return p.display()


# 3. Details of ...

class RHRoomBookingRoomDetails( RHRoomBookingBase ):

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._room = self._target = locator.getObject()

        session = self._websession
        self._afterActionSucceeded = session.getVar( "actionSucceeded" )
        self._afterDeletionFailed = session.getVar( "deletionFailed" )
        self._formMode = session.getVar( "formMode" )

        self._searchingStartDT = self._searchingEndDT = None
        if not params.get( 'calendarMonths' ):
            self._searchingStartDT = session.getVar( "defaultStartDT" )
            self._searchingEndDT = session.getVar( "defaultEndDT" )

        self._clearSessionState()

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomDetails( self )
        return p.display()

class RHRoomBookingRoomStats( RHRoomBookingBase ):

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._period = params.get("period","pastmonth")
        self._room = self._target = locator.getObject()

    def _businessLogic( self ):
        self._kpiAverageOccupation = self._room.getMyAverageOccupation(self._period)
        self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms()
        self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms()
        self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity()
        # Bookings
        st = ReservationBase.getRoomReservationStats(self._room)
        self._booking_stats = st
        self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomStats( self )
        return p.display()

class RHRoomBookingBookingDetails( RHRoomBookingBase ):

    def _checkParams( self, params ):

        locator = locators.WebLocator()
        locator.setRoomBooking( params )
        self._resv = self._target = locator.getObject()

        self._afterActionSucceeded = self._websession.getVar( "actionSucceeded" )
        self._title = self._websession.getVar( "title" )
        self._description = self._websession.getVar( "description" )
        self._afterDeletionFailed = self._websession.getVar( "deletionFailed" )

        self._clearSessionState()

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingDetails( self )
        return p.display()

# 4. New

class RHRoomBookingBookingForm( RHRoomBookingBase ):

    def _checkParams( self, params ):
        session = self._websession  # Just an alias
        self._thereAreConflicts = session.getVar( 'thereAreConflicts' )
        self._skipConflicting = False

        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ) or params.get( "afterCalPreview" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.getVar( "candDataInSession" ):
            self._dataFrom = CandidateDataFrom.SESSION

        # Reservation ID?
        resvID = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            resvID = session.getVar( "resvID" )
            roomLocation = session.getVar( "roomLocation" )
        else:
            resvID = params.get( "resvID" )
            if isinstance( resvID, list ): resvID = resvID[0]
            roomLocation = params.get( "roomLocation" )
            if isinstance( roomLocation, list ): roomLocation = roomLocation[0]
        if resvID == "None": resvID = None
        if resvID: resvID = int( resvID )

        # FORM MODE?
        if resvID:
            self._formMode = FormMode.MODIF
        else:
            self._formMode = FormMode.NEW

        # SHOW ERRORS?
        self._showErrors = self._websession.getVar( "showErrors" )
        if self._showErrors:
            self._errors = self._websession.getVar( "errors" )

        # CREATE CANDIDATE OBJECT
        candResv = None

        if self._formMode == FormMode.NEW:
            if self._dataFrom == CandidateDataFrom.SESSION:
                candResv = self._loadResvCandidateFromSession( None, params )
            elif self._dataFrom == CandidateDataFrom.PARAMS:
                candResv = self._loadResvCandidateFromParams( None, params )
            else:
                candResv = self._loadResvCandidateFromDefaults( params )

        if self._formMode == FormMode.MODIF:
            import copy
            candResv = copy.copy(CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation ))
            if self._dataFrom == CandidateDataFrom.PARAMS:
                self._loadResvCandidateFromParams( candResv, params )
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadResvCandidateFromSession( candResv, params )

        self._errors = session.getVar( "errors" )
        self._candResv = candResv

        self._clearSessionState()


    def _checkProtection( self ):

        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            if not self._candResv.room.isActive and not self._getUser().isAdmin():
                raise MaKaCError( "You are not authorized to book this room." )

            if not self._candResv.room.canBook( self._getUser() ) and not self._candResv.room.canPrebook( self._getUser() ):
                raise MaKaCError( "You are not authorized to book this room." )

            if self._formMode == FormMode.MODIF:
                if not self._candResv.canModify( self.getAW() ):
                    raise MaKaCError( "You are not authorized to take this action." )

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingForm( self )
        return p.display()

class RHRoomBookingCloneBooking( RHRoomBookingBase ):
    """
    Performs open a new booking form with the data of an already existing booking.
    """

    def _checkParams( self, params ):
        session = self._websession  # Just an alias

        # DATA FROM
        session.setVar( "candDataInSession", True )

        self._formMode = FormMode.NEW

        # Reservation ID
        resvID = int(params.get( "resvID" ))

        # CREATE CANDIDATE OBJECT
        candResv = CrossLocationQueries.getReservations( resvID = resvID)
        if type(candResv) == list:
            candResv=candResv[0]
        self._saveResvCandidateToSession(candResv)
        self._room = candResv.room


    def _process( self ):
        self._redirect(urlHandlers.UHRoomBookingBookingForm.getURL(self._room))


class RHRoomBookingSaveBooking( RHRoomBookingBase ):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to booking details, otherwise returns to booking form.
    """

    def _checkParams( self, params ):

        resvID = params.get( "resvID" )
        roomLocation = params.get( "roomLocation" )
        self._answer = params.get( "answer", None )
        self._skipConflicting = False

        # forceAddition is set by the confirmation dialog, so that
        # prebookings that conflict with other prebookings are
        # silently added

        self._forceAddition = params.get("forceAddition","False")
        if self._forceAddition == 'True':
            self._forceAddition = True
        else:
            self._forceAddition = False

        candResv = None
        if resvID:
            self._formMode = FormMode.MODIF
            resvID = int( resvID )
            _candResv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
            self._orig_candResv = _candResv

            import copy
            candResv = copy.copy(_candResv)

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession( candResv, params )
            else:
                self._loadResvCandidateFromParams( candResv, params )

            self._resvID = resvID

        else:
            self._formMode = FormMode.NEW
            candResv = Location.parse( roomLocation ).factory.newReservation()
            candResv.createdDT = datetime.now()
            candResv.createdBy = str( self._getUser().id )
            candResv.isRejected = False
            candResv.isCancelled = False

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession( candResv, params )
            else:
                self._loadResvCandidateFromParams( candResv, params )

            self._resvID = None


        self._candResv = candResv

        self._params = params
        self._clearSessionState()


    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)

        if not self._candResv.room.isActive and not self._getUser().isAdmin():
            raise MaKaCError( "You are not authorized to book this room." )

        if self._formMode == FormMode.MODIF:
            if not self._candResv.canModify( self.getAW() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _businessLogic( self ):

        candResv = self._candResv
        self._emailsToBeSent = []
        self._confirmAdditionFirst = False;

        # Set confirmation status
        candResv.isConfirmed = True
        user = self._getUser()
        if not candResv.room.canBook( user ):
            candResv.isConfirmed = False


        errors = self._getErrorsOfResvCandidate( candResv )
        session = self._websession

        if not errors and self._answer != 'No':

            # If we're dealing with an unapproved pre-booking
            if not candResv.isConfirmed and not self._forceAddition:

                candResv.isConfirmed = None;
                # find pre-booking collisions
                self._collisions = candResv.getCollisions(sansID = candResv.id)

                candResv.isConfirmed = False

                # are there any collisions?
                if len( self._collisions ) > 0:
                    # save the reservation to the session
                    self._saveResvCandidateToSession( candResv )
                    # ask for confirmation about the pre-booking
                    self._confirmAdditionFirst = True


            # approved pre-booking or booking
            if not self._confirmAdditionFirst:

                # Form is OK and (no conflicts or skip conflicts)
                if self._formMode == FormMode.NEW:
                    candResv.insert()
                    self._emailsToBeSent+=candResv.notifyAboutNewReservation()
                    if candResv.isConfirmed:
                        session.setVar( "title", 'You have successfully made a booking.' )
                        session.setVar( "description", 'NOTE: Your booking is complete. However, be <b>aware</b> that in special cases the person responsible for a room may reject your booking. In that case you would be instantly notified by e-mail.' )
                    else:
                        session.setVar( "title", 'You have successfully made a <span style="color: Red;">PRE</span>-booking.' )
                        session.setVar( "description", 'NOTE: PRE-bookings are subject to acceptance or rejection. Expect an e-mail with acceptance/rejection information.' )
                elif self._formMode == FormMode.MODIF:
                    if self._forceAddition:
                        self._loadResvCandidateFromSession( self._orig_candResv, self._params )
                    else:
                        self._loadResvCandidateFromParams( self._orig_candResv, self._params )
                    self._orig_candResv.update()
                    self._emailsToBeSent += self._orig_candResv.notifyAboutUpdate()
                    session.setVar( "title", 'Booking updated.' )
                    session.setVar( "description", 'Please review details below.' )
                session.setVar( "actionSucceeded", True )


        else:
            session.setVar( "candDataInSession", True )
            session.setVar( "errors", errors )

            if self._answer == 'No':
                session.setVar( "actionSucceeded", True )
            else:
                session.setVar( "actionSucceeded", False )
                session.setVar( "showErrors", True )
                session.setVar( "thereAreConflicts", self._thereAreConflicts )

            self._saveResvCandidateToSession( candResv )

        # Form is not properly filled OR there are conflicts
        self._errors = errors

    def _process( self ):

        self._businessLogic()

        if self._errors or self._answer == 'No':
            url = urlHandlers.UHRoomBookingBookingForm.getURL( self._candResv.room, resvID=self._resvID )
        elif self._confirmAdditionFirst:
            p = roomBooking_wp.WPRoomBookingConfirmBooking( self )
            return p.display()
        else:
            url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._candResv )

        self._redirect( url )


class RHRoomBookingRoomForm( RHRoomBookingAdminBase ):
    """
    Form for creating NEW and MODIFICATION of an existing room.
    """

    def _checkParams( self, params ):
        session = self._websession  # Just an alias

        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.getVar( "candDataInSession" ):
            self._dataFrom = CandidateDataFrom.SESSION

        # Room ID?
        roomID = None
        roomLocation = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            roomID = session.getVar( "roomID" )
            roomLocation = session.getVar( "roomLocation" )
        else:
            roomID = params.get( "roomID" )
            roomLocation = params.get( "roomLocation" )
        if roomID: roomID = int( roomID )

        # FORM MODE?
        if roomID:
            self._formMode = FormMode.MODIF
        else:
            self._formMode = FormMode.NEW

        # SHOW ERRORS?
        self._showErrors = self._websession.getVar( "showErrors" )
        if self._showErrors:
            self._errors = self._websession.getVar( "errors" )

        # CREATE CANDIDATE OBJECT
        candRoom = None

        if self._formMode == FormMode.NEW:
            locationName = params.get("roomLocation", "")
            location = Location.parse(locationName)
            if str(location) == "None":
                # Room should be inserted into default backend => using Factory
                candRoom = Factory.newRoom()
            else:
                candRoom = location.newRoom()
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadRoomCandidateFromSession( candRoom )
            else:
                self._loadRoomCandidateFromDefaults( candRoom )

        if self._formMode == FormMode.MODIF:
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )

            if self._dataFrom == CandidateDataFrom.PARAMS:
                self._loadRoomCandidateFromParams( candRoom, params )
            if self._dataFrom == CandidateDataFrom.SESSION:
                self._loadRoomCandidateFromSession( candRoom )

        self._errors = session.getVar( "errors" )

        # After searching for responsible
        if params.get( 'selectedPrincipals' ):
            candRoom.responsibleId = params['selectedPrincipals']

        self._candRoom = self._target = candRoom
        self._clearSessionState()

    def _process( self ):
        p = admins.WPRoomBookingRoomForm( self )
        return p.display()

class RHRoomBookingSaveRoom( RHRoomBookingAdminBase ):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to room details, otherwise returns to room form.
    """

    def _uploadPhotos( self, candRoom, params ):
        if params.get( "largePhotoPath" ) and params.get( "smallPhotoPath" ):
            candRoom.savePhoto( params["largePhotoPath"] )
            candRoom.saveSmallPhoto( params["smallPhotoPath"] )

    def _checkParams( self, params ):
        roomID = params.get( "roomID" )
        roomLocation = params.get( "roomLocation" )

        candRoom = None
        if roomID:
            self._formMode = FormMode.MODIF
            if roomID: roomID = int( roomID )
            candRoom = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        else:
            self._formMode = FormMode.NEW
            if roomLocation:
                name = Location.parse(roomLocation).friendlyName
            else:
                name = Location.getDefaultLocation().friendlyName
            location = Location.parse(name)
            candRoom = location.newRoom()
            candRoom.locationName = name

        self._loadRoomCandidateFromParams( candRoom, params )
        self._candRoom = self._target = candRoom
        self._params = params

    def _process( self ):
        candRoom = self._candRoom
        params = self._params

        errors = self._getErrorsOfRoomCandidate( candRoom )
        if not errors:
            # Succeeded
            if self._formMode == FormMode.MODIF:
                candRoom.update()
                # if responsibleId changed
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingRoomDetails.getURL(candRoom)

            elif self._formMode == FormMode.NEW:
                candRoom.insert()
                candRoom.notifyAboutResponsibility()
                url = urlHandlers.UHRoomBookingAdminLocation.getURL(Location.parse(candRoom.locationName), actionSucceeded = True)

            self._uploadPhotos( candRoom, params )
            self._websession.setVar( "actionSucceeded", True )
            self._websession.setVar( "formMode", self._formMode )
            self._redirect( url ) # Redirect to room DETAILS
        else:
            # Failed
            self._websession.setVar( "actionSucceeded", False )
            self._websession.setVar( "candDataInSession", True )
            self._websession.setVar( "errors", errors )
            self._websession.setVar( "showErrors", True )

            self._saveRoomCandidateToSession( candRoom )
            url = urlHandlers.UHRoomBookingRoomForm.getURL( None )
            self._redirect( url ) # Redirect again to FORM


class RHRoomBookingDeleteRoom( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        roomID = params.get( "roomID" )
        roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        self._room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        self._target = self._room

    def _process( self ):
        room = self._room
        # Check whether deletion is possible
        liveResv = room.getLiveReservations()
        if len( liveResv ) == 0:
            # Possible - delete
            for resv in room.getReservations():
                resv.remove()
            room.remove()
            self._websession.setVar( 'title', "Room has been deleted." )
            self._websession.setVar( 'description', "You have successfully deleted the room. All its archival, cancelled and rejected bookings have also been deleted." )
            url = urlHandlers.UHRoomBookingStatement.getURL()
            self._redirect( url ) # Redirect to deletion confirmation
        else:
            # Impossible
            self._websession.setVar( 'deletionFailed', True )
            url = urlHandlers.UHRoomBookingRoomDetails.getURL( room )
            self._redirect( url ) # Redirect to room DETAILS

class RHRoomBookingDeleteBooking( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _process( self ):
        # Booking deletion is always possible - just delete
        self._resv.remove()
        self._websession.setVar( 'title', "Booking has been deleted." )
        self._websession.setVar( 'description', "You have successfully deleted the booking." )
        url = urlHandlers.UHRoomBookingStatement.getURL()
        self._redirect( url ) # Redirect to deletion confirmation

class RHRoomBookingCancelBooking( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only owner (the one who created) and admin can CANCEL
        # (Responsible can not cancel a booking!)
        if ( not self._resv.isOwnedBy( user ) ) and \
            ( not self._getUser().isAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        # Booking deletion is always possible - just delete
        self._emailsToBeSent = []
        self._resv.cancel()    # Just sets isCancel = True
        self._resv.update(udpateReservationIndex=False)
        self._emailsToBeSent += self._resv.notifyAboutCancellation()

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Booking has been cancelled." )
        self._websession.setVar( 'description', "You have successfully cancelled the booking." )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingCancelBookingOccurrence( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        date = params.get( "date" )

        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._date = parse_date( date )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only user/admin can cancell a booking occurrence
        # (Owner can not reject his own booking, he should cancel instead)
        if self._resv.createdBy != user.getId() and (not user.isAdmin()):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._emailsToBeSent = []
        self._resv.excludeDay( self._date, unindex=True )
        self._resv.update(udpateReservationIndex=False)
        self._emailsToBeSent += self._resv.notifyAboutCancellation( date = self._date )

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Selected occurrence has been cancelled." )
        self._websession.setVar( 'description', "YOu have successfully cancelled an occurrence of this booking." )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingRejectBooking( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        reason = params.get( "reason" )

        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._resv.rejectionReason = reason
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if ( not self._resv.room.isOwnedBy( user ) ) and \
            ( not self._getUser().isAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._emailsToBeSent = []
        self._resv.reject()    # Just sets isRejected = True
        self._resv.update(udpateReservationIndex=False)
        self._emailsToBeSent += self._resv.notifyAboutRejection()

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Booking has been rejected." )
        self._websession.setVar( 'description', "NOTE: rejection e-mail has been sent to the user. However, it's advisable to <strong>inform</strong> the user directly. Note that users often don't read e-mails." )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingRejectALlConflicting( RHRoomBookingBase ):

#    def _checkParams( self , params ):
#        pass

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if ( not user.getRooms() ) and \
            ( not self._getUser().isAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        userRooms = self._getUser().getRooms()
        self._emailsToBeSent = []

        resvEx = ReservationBase()
        resvEx.isConfirmed = False
        resvEx.isRejected = False
        resvEx.isCancelled = False

        resvs = CrossLocationQueries.getReservations( resvExample = resvEx, rooms = userRooms )

        counter = 0
        for resv in resvs:
            if resv.getCollisions( sansID = resv.id, boolResult = True ):
                resv.rejectionReason = "Your PRE-booking conflicted with exiting booking. (Please note it IS possible even if you were the first one to PRE-book the room)."
                resv.reject()    # Just sets isRejected = True
                resv.update()
                self._emailsToBeSent += resv.notifyAboutRejection()
                counter += 1
        self._websession.setVar( 'prebookingsRejected', True )
        if counter > 0:
            self._websession.setVar( 'title', str( counter ) + " conflicting PRE-bookings have been rejected." )
            self._websession.setVar( 'description', "Rejection e-mails have been sent to the users, with explanation that their PRE-bookings conflicted with the present confirmed bookings." )
        else:
            self._websession.setVar( 'title', "There are no conflicting PRE-bookings for your rooms." )
            self._websession.setVar( 'description', "" )
        url = urlHandlers.UHRoomBookingBookingList.getURL( ofMyRooms = True, onlyPrebookings = True, autoCriteria = True )
        self._redirect( url ) # Redirect to booking details

class RHRoomBookingAcceptBooking( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can ACCEPT
        if ( not self._resv.room.isOwnedBy( user ) ) and \
            ( not self._getUser().isAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._emailsToBeSent = []
        session = self._websession
        if len( self._resv.getCollisions( sansID = self._resv.id ) ) == 0:
            # No conflicts
            self._resv.isConfirmed = True
            self._resv.update(False)
            self._emailsToBeSent += self._resv.notifyAboutConfirmation()

            session.setVar( 'actionSucceeded', True )
            session.setVar( 'title', "Booking has been accepted." )
            session.setVar( 'description', "NOTE: confirmation e-mail has been sent to the user." )
            url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
            self._redirect( url ) # Redirect to booking details
        else:
            errors = ["PRE-Booking conflicts with other (confirmed) bookings."]
            session.setVar( "actionSucceeded", False )
            session.setVar( "candDataInSession", True )
            session.setVar( "errors", errors )
            session.setVar( "showErrors", True )
            session.setVar( "thereAreConflicts", True )

            session.setVar( 'title', "PRE-Booking conflicts with other (confirmed) bookings." )
            session.setVar( 'description', "" )

            self._formMode = FormMode.MODIF
            self._saveResvCandidateToSession( self._resv )
            url = urlHandlers.UHRoomBookingBookingForm.getURL( self._resv.room )
            self._redirect( url ) # Redirect to booking details


class RHRoomBookingStatement( RHRoomBookingBase ):

    def _checkParams( self , params ):
        session = self._websession
        self._title = session.getVar( 'title' )
        self._description = session.getVar( 'description' )
        session.setVar( 'title', None )
        session.setVar( 'description', None )

    def _process( self ):
        return roomBooking_wp.WPRoomBookingStatement( self ).display()

class RHRoomBookingAdmin( RHRoomBookingAdminBase ):

    def _process( self ):
        return admins.WPRoomBookingAdmin( self ).display()

class RHRoomBookingAdminLocation( RHRoomBookingAdminBase ):

    def _checkParams( self, params ):
        self._withKPI = False
        if params.get( 'withKPI' ) == 'True':
            self._withKPI = True
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

        if params.get("actionSucceeded", None):
            self._actionSucceeded = True
        else:
            self._actionSucceeded = False

    def _process( self ):

        if self._withKPI:
            self._kpiAverageOccupation = RoomBase.getAverageOccupation(location=self._location.friendlyName)
            self._kpiTotalRooms = RoomBase.getNumberOfRooms(location=self._location.friendlyName)
            self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms(location=self._location.friendlyName)
            self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms(location=self._location.friendlyName)
            self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity(location=self._location.friendlyName)

            # Bookings

            st = ReservationBase.getReservationStats(location=self._location.friendlyName)
            self._booking_stats = st
            self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

        return admins.WPRoomBookingAdminLocation( self, self._location, actionSucceeded = self._actionSucceeded ).display()


class RHRoomBookingSetDefaultLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._defaultLocation = params["defaultLocation"]

    def _process( self ):
        Location.setDefaultLocation( self._defaultLocation )
        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )

class RHRoomBookingSaveLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._locationName = params["newLocationName"].strip()
        self._pluginClass = None
        name = params.get("pluginName","default")
        plugs = plugins.getPluginsByType("RoomBooking")
        for plug in plugs:
            if plug.pluginName == name:
                self._pluginClass = plug.roombooking.getRBClass()
        if self._pluginClass == None:
            raise MaKaCError( "%s: Cannot find requested plugin" % name )

    def _process( self ):
        if self._locationName:
            location = Location( self._locationName, self._pluginClass )
            Location.insertLocation( location )

        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )

class RHRoomBookingDeleteLocation( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._locationName = params["removeLocationName"]

    def _process( self ):

        if self._locationName:
            Location.removeLocation( self._locationName )
        url = urlHandlers.UHRoomBookingAdmin.getURL()
        self._redirect( url )

class RHRoomBookingSaveEquipment( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._eq = params["newEquipmentName"].strip()
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        if self._eq:
            self._location.factory.getEquipmentManager().insertEquipment( self._eq, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingDeleteEquipment( RHRoomBookingAdminBase ):

    def _checkParams( self , params ):
        self._eq = params["removeEquipmentName"]
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        self._location.factory.getEquipmentManager().removeEquipment( self._eq, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingSaveCustomAttribute( RHRoomBookingAdminBase ): # + additional

    def _checkParams( self , params ):
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

        self._newAttr = None
        if params.get( "newCustomAttributeName" ):
            attrName = params["newCustomAttributeName"].strip()
            if attrName:
                attrIsReq = False
                if params.get( "newCustomAttributeIsRequired" ) == "on":
                    attrIsReq = True
                attrIsHidden = False
                if params.get( "newCustomAttributeIsHidden" ) == "on":
                    attrIsHidden = True
                self._newAttr = { \
                    'name': attrName,
                    'type': 'str',
                    'required': attrIsReq,
                    'hidden': attrIsHidden }

        # Set "required" for _all_ custom attributes
        manager = self._location.factory.getCustomAttributesManager()
        for ca in manager.getAttributes(location=self._location.friendlyName):
            required = hidden = False
            # Try to find in params (found => required == True)
            for k in params.iterkeys():
                if k[0:10] == "cattr_req_":
                    attrName = k[10:100].strip()
                    if attrName == ca['name']:
                        required = True
                if k[0:10] == "cattr_hid_":
                    attrName = k[10:100].strip()
                    if attrName == ca['name']:
                        hidden = True
            manager.setRequired( ca['name'], required, location=self._location.friendlyName )
            manager.setHidden( ca['name'], hidden, location=self._location.friendlyName )

    def _process( self ):
        if self._newAttr:
            self._location.factory.getCustomAttributesManager().insertAttribute( self._newAttr, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingDeleteCustomAttribute( RHRoomBookingAdminBase ):  # + additional

    def _checkParams( self , params ):
        self._attr = params["removeCustomAttributeName"]
        name = params.get("locationId","")
        self._location = Location.parse(name)
        if str(self._location) == "None":
            raise MaKaCError( "%s: Unknown Location" % name )

    def _process( self ):
        self._location.factory.getCustomAttributesManager().removeAttribute( self._attr, location=self._location.friendlyName )
        url = urlHandlers.UHRoomBookingAdminLocation.getURL(self._location)
        self._redirect( url )

class RHRoomBookingSendRoomPhoto( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self.fileName = params['photoId'] + ".jpg"
        self.small = params.get( 'small' ) == 'True' # Large by default

    def _process( self ):
        cfg = Config.getInstance()

        filePath = cfg.getRoomPhotosDir()
        if self.small:
            filePath = cfg.getRoomSmallPhotosDir()
        fullPath = os.path.join( filePath, self.fileName )

        self._req.content_type = "image/jpeg"
        #self._req.headers_out["Content-Disposition"] = "inline; filename=\"%s\"" % self.fileName
        self._req.sendfile( fullPath )

from MaKaC.common.utils import isWeekend

class RHRoomBookingGetDateWarning( RHRoomBookingBase ):

    def _checkParams( self, params ):
        try:
            self._checkParamsRepeatingPeriod( params )
        except:
            pass

    def addRandom( self, s ):
        return s
        #import random
        #return str( int( random.random() * 1000 ) ) + " | " + s

    def _process( self ):
        if not self._startDT or not self._endDT:
            return self.addRandom( " " )

        if  HolidaysHolder.isWorkingDay( self._startDT ) and \
            HolidaysHolder.isWorkingDay( self._endDT ):
            return self.addRandom( " " )

        if isWeekend( self._startDT ) or isWeekend( self._endDT ):
            return self.addRandom( "Warning: weekend chosen" )

        return self.addRandom( "Warning: holidays chosen" )


class RHRoomBookingGetRoomSelectList( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self.location = params.get( 'locationName' )
        self.forSubEvents = params.get( 'forSubEvents' ) == 'True'

    def _process( self ):

        self._roomList = []
        if self.location:
            self._roomList = CrossLocationQueries.getRooms( location = self.location )
        self._locationRoom = ""

        from MaKaC.webinterface import wcomponents
        if self.forSubEvents:
            p = wcomponents.WRoomBookingRoomSelectList4SubEvents( self )
        else:
            p = wcomponents.WRoomBookingRoomSelectList( self )

        return p.getHTML( self.getRequestParams() )

        #return "<div style='background-color: red;'>&nbsp;&nbsp;&nbsp;&nbsp;</div>"

class RHRoomBookingRejectBookingOccurrence( RHRoomBookingBase ):

    def _checkParams( self , params ):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        reason = params.get( "reason" )
        date = params.get( "date" )

        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._rejectionReason = reason
        self._date = parse_date( date )
        self._target = self._resv

    def _checkProtection( self ):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if ( not self._resv.room.isOwnedBy( user ) ) and \
            ( not self._getUser().isAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._emailsToBeSent = []
        self._resv.excludeDay( self._date, unindex=True )
        self._resv.update(udpateReservationIndex=False)
        self._emailsToBeSent += self._resv.notifyAboutRejection( date = self._date, reason = self._rejectionReason )

        self._websession.setVar( 'actionSucceeded', True )
        self._websession.setVar( 'title', "Selected occurrence of this booking has been rejected." )
        self._websession.setVar( 'description', "NOTE: rejection e-mail has been sent to the user. " )
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details
