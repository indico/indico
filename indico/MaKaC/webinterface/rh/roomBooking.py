# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from flask import request, session

from MaKaC.plugins.base import pluginId
# Most of the following imports are probably not necessary - to clean

import os
import time
from collections import defaultdict

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.locators as locators
from indico.core.config import Config
from MaKaC.webinterface.rh.base import RoomBookingDBMixin, RHRoomBookingProtected
from datetime import datetime, timedelta, date
from MaKaC.common.utils import validMail, setValidEmailSeparators, parseDate
from MaKaC.common.datetimeParser import parse_date
from indico.web.flask.util import send_file

# The following are room booking related

import MaKaC.webinterface.pages.roomBooking as roomBooking_wp
import MaKaC.webinterface.pages.admins as admins
from MaKaC.rb_room import RoomBase
from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.rb_location import CrossLocationQueries, RoomGUID, Location
from MaKaC.rb_tools import intd, FormMode, dateAdvanceAllowed
from MaKaC.errors import MaKaCError, FormValuesError, NoReportError
from MaKaC.plugins import PluginLoader
from MaKaC import plugins
from MaKaC.plugins.RoomBooking.default.reservation import ResvHistoryEntry
from MaKaC.plugins.RoomBooking.default.room import Room
from MaKaC.plugins.RoomBooking.rb_roomblocking import RoomBlockingBase
from MaKaC.plugins.RoomBooking.default.roomblocking import (RoomBlockingPrincipal,
                                                            BlockedRoom)
from MaKaC.plugins.RoomBooking.common import getRoomBookingOption
from MaKaC.common.mail import GenericMailer
from MaKaC.common.cache import GenericCache

class CandidateDataFrom( object ):
    DEFAULTS, PARAMS, SESSION = xrange( 3 )

# 0. Base classes

class RoomBookingAvailabilityParamsMixin:
    def _checkParamsRepeatingPeriod( self, params ):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """

        sDay = params.get( "sDay" )
        eDay = params.get( "eDay" )
        sMonth = params.get( "sMonth" )
        eMonth = params.get( "eMonth" )
        sYear = params.get( "sYear" )
        eYear = params.get( "eYear" )

        if sDay and len( sDay.strip() ) > 0:
            sDay = int( sDay.strip() )

        if eDay and len( eDay.strip() ) > 0:
            eDay = int( eDay.strip() )

        if sMonth and len( sMonth.strip() ) > 0:
            sMonth = int( sMonth.strip() )

#        if sYear and sMonth and sDay:
#            # For format checking
#            try:
#                time.strptime(sDay.strip() + "/" + sMonth.strip() + "/" + sYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The Start Date must be of the form DD/MM/YYYY and must be a valid date."))

        if eMonth and len( eMonth.strip() ) > 0:
            eMonth = int( eMonth.strip() )

        if sYear and len( sYear.strip() ) > 0:
            sYear = int( sYear.strip() )

        if eYear and len( eYear.strip() ) > 0:
            eYear = int( eYear.strip() )

#        if eYear and eMonth and eDay:
#            # For format checking
#            try:
#                time.strptime(eDay.strip() + "/" + eMonth.strip() + "/" + eYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The End Date must be of the form DD/MM/YYYY and must be a valid date."))


        sTime = params.get( "sTime" )
        if sTime and len( sTime.strip() ) > 0:
            sTime = sTime.strip()
        eTime = params.get( "eTime" )
        if eTime and len( eTime.strip() ) > 0:
            eTime = eTime.strip()

        # process sTime and eTime
        if sTime and eTime:

            try:
                time.strptime(sTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The Start Time must be of the form HH:MM and must be a valid time."))

            t = sTime.split( ':' )
            sHour = int( t[0] )
            sMinute = int( t[1] )

            try:
                time.strptime(eTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The End Time must be of the form HH:MM and must be a valid time."))

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

class RHRoomBookingBase( RoomBookingAvailabilityParamsMixin, RoomBookingDBMixin, RHRoomBookingProtected ):
    """
    All room booking related hanlders are derived from this class.
    This gives them:
    - several general use methods
    - login-protection
    - auto connecting/disconnecting from room booking db
    """

    def _checkProtection( self ):
        RHRoomBookingProtected._checkProtection(self)

    def _clearSessionState(self):
        session.pop('rbActionSucceeded', None)
        session.pop('rbTitle', None)
        session.pop('rbDescription', None)
        session.pop('rbDeletionFailed', None)
        session.pop('rbFormMode', None)
        session.pop('rbCandDataInSession', None)
        session.pop('rbShowErrors', None)
        session.pop('rbErrors', None)
        session.pop('rbThereAreConflicts', None)
        session.pop('rbRoomID', None)
        session.pop('rbRoomLocation', None)
        session.pop('rbResvID', None)

    # Room

    def _saveRoomCandidateToSession( self, c ):
        # TODO: is this method needed anymore??
        if self._formMode == FormMode.MODIF:
            session['rbRoomID'] = c.id
            session['rbRoomLocation'] = c.locationName

        session['rbRoomCand'] = {
            "name": c.name,
            "site": c.site,
            "building": c.building,
            "floor": c.floor,
            "roomNr": c.roomNr,
            "latitude": c.latitude,
            "longitude": c.longitude,

            "isActive": c.isActive,
            "isReservable": c.isReservable,
            "resvsNeedConfirmation": c.resvsNeedConfirmation,
            "resvStartNotification": c.resvStartNotification,
            "resvStartNotificationBefore": c.resvStartNotificationBefore,
            "resvEndNotification": c.resvEndNotification,
            "resvNotificationToResponsible": c.resvNotificationToResponsible,
            "resvNotificationAssistance": c.resvNotificationAssistance,

            "responsibleId": c.responsibleId,
            "whereIsKey": c.whereIsKey,
            "telephone": c.telephone,

            "capacity": c.capacity,
            "division": c.division,
            "surfaceArea": c.surfaceArea,
            "maxAdvanceDays": c.maxAdvanceDays,
            "comments": c.comments,

            "equipment": c.getEquipment(),
            "cattrs": dict(c.customAtts.iteritems())
        }


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

        try:
            float(c.longitude)
        except ValueError:
            errors.append("Longitude must be a number")

        try:
            float(c.latitude)
        except ValueError:
            errors.append("Latitude must be a number")

        try:
            for dailyBookablePeriod in c.getDailyBookablePeriods():
                if datetime.strptime(dailyBookablePeriod.getStartTime(), "%H:%M").time() > datetime.strptime(dailyBookablePeriod.getEndTime(), "%H:%M").time():
                    errors.append("period start time should be before end time in daily availability period field")
                    break
        except ValueError:
            errors.append("Daily availability periods must be in correct time format 'HH:MM'")

        params = self._params
        if ( params['largePhotoPath'] != '' ) ^ ( params['smallPhotoPath'] != '' ):
            errors.append( "Either upload both photos or none")

        # Custom attributes
        manager = CrossLocationQueries.getCustomAttributesManager( c.locationName )
        for ca in manager.getAttributes( location = c.locationName ):
            if ca['name'] == 'notification email' :
                if c.customAtts[ 'notification email' ] and not validMail(c.customAtts['notification email']) :
                    errors.append( "Invalid format for the notification email" )
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
        candRoom.longitude = ''
        candRoom.latitude = ''

        candRoom.capacity = 20
        candRoom.site = ''
        candRoom.division = None
        candRoom.isReservable = True
        candRoom.resvsNeedConfirmation = False
        candRoom.resvStartNotification = False
        candRoom.resvStartNotificationBefore = None
        candRoom.resvEndNotification = False
        candRoom.resvNotificationToResponsible = False
        candRoom.resvNotificationAssistance = False
        candRoom.photoId = None
        candRoom.externalId = None

        candRoom.telephone = ''      # str
        candRoom.surfaceArea = None
        candRoom.maxAdvanceDays = 0
        candRoom.whereIsKey = ''
        candRoom.comments = ''
        candRoom.responsibleId = None

    def _loadRoomCandidateFromSession(self, candRoom):
        sessionCand = session['rbRoomCand']

        candRoom.name = sessionCand["name"]
        candRoom.site = sessionCand["site"]
        candRoom.building = intd(sessionCand["building"])
        candRoom.floor = sessionCand["floor"]
        candRoom.roomNr = sessionCand["roomNr"]
        candRoom.latitude = sessionCand["latitude"]
        candRoom.longitude = sessionCand["longitude"]

        candRoom.isActive = bool(sessionCand["isActive"])
        candRoom.isReservable = bool(sessionCand["isReservable"])
        candRoom.resvsNeedConfirmation = bool(sessionCand["resvsNeedConfirmation"])
        candRoom.resvStartNotification = sessionCand["resvStartNotification"]
        candRoom.resvStartNotificationBefore = sessionCand["resvStartNotificationBefore"]
        candRoom.resvEndNotification = bool(sessionCand["resvEndNotification"])
        candRoom.resvNotificationToResponsible = bool(sessionCand["resvNotificationToResponsible"])
        candRoom.resvNotificationAssistance = bool(sessionCand["resvNotificationAssistance"])

        candRoom.responsibleId = sessionCand["responsibleId"]
        candRoom.whereIsKey = sessionCand["whereIsKey"]
        candRoom.telephone = sessionCand["telephone"]

        candRoom.capacity = intd(sessionCand["capacity"])
        candRoom.division = sessionCand["division"]
        candRoom.surfaceArea = intd(sessionCand["surfaceArea"])
        candRoom.maxAdvanceDays = intd(sessionCand["maxAdvanceDays"])
        candRoom.comments = sessionCand["comments"]

        candRoom.setEquipment(sessionCand["equipment"])

        manager = CrossLocationQueries.getCustomAttributesManager( candRoom.locationName )
        for ca in manager.getAttributes( location = candRoom.locationName ):
            value = sessionCand['cattrs'].get(ca['name'])
            if value != None:
                if ca['name'] == 'notification email' :
                    candRoom.customAtts[ 'notification email' ] = setValidEmailSeparators(value)
                else :
                    candRoom.customAtts[ ca['name'] ] = value


    def _loadRoomCandidateFromParams( self, candRoom, params ):
        candRoom.name = params.get( "name" )
        candRoom.site = params.get( "site" )
        candRoom.building = intd( params.get( "building" ) )
        candRoom.floor = params.get( "floor" )
        candRoom.roomNr = params.get( "roomNr" )
        candRoom.latitude = params.get( "latitude" )
        candRoom.longitude = params.get( "longitude" )

        candRoom.isActive = bool( params.get( "isActive" ) ) # Safe
        candRoom.isReservable = bool( params.get( "isReservable" ) ) # Safe
        candRoom.resvsNeedConfirmation = bool( params.get( "resvsNeedConfirmation" ) ) # Safe
        candRoom.resvStartNotification = bool( params.get( "resvStartNotification" ) )
        tmp = params.get("resvStartNotificationBefore")
        candRoom.resvStartNotificationBefore = intd(tmp) if tmp else None
        candRoom.resvEndNotification = bool( params.get( "resvEndNotification" ) )
        candRoom.resvNotificationToResponsible = bool(params.get('resvNotificationToResponsible'))
        candRoom.resvNotificationAssistance = bool(params.get('resvNotificationAssistance'))


        candRoom.responsibleId = params.get( "responsibleId" )
        if candRoom.responsibleId == "None":
            candRoom.responsibleId = None
        candRoom.whereIsKey = params.get( "whereIsKey" )
        candRoom.telephone = params.get( "telephone" )

        candRoom.capacity = intd( params.get( "capacity" ) )
        candRoom.division = params.get( "division" )
        candRoom.surfaceArea = intd( params.get( "surfaceArea" ) )
        candRoom.comments = params.get( "comments" )
        candRoom.maxAdvanceDays = intd(params.get( "maxAdvanceDays" ))
        candRoom.clearNonBookableDates()
        candRoom.clearDailyBookablePeriods()

        for periodNumber in range(int(params.get("nonBookablePeriodCounter"))):
            if params.get("startDateNonBookablePeriod" + str(periodNumber)):
                # adding formated data to be compatible with the old DB version
                try:
                    candRoom.addNonBookableDates(datetime.strptime(params.get("startDateNonBookablePeriod" + str(periodNumber)), '%d/%m/%Y %H:%M'),
                                             datetime.strptime(params.get("endDateNonBookablePeriod" + str(periodNumber)), '%d/%m/%Y %H:%M'))
                except ValueError:
                    continue

        for periodNumber in range(int(params.get("dailyBookablePeriodCounter"))):
            if params.get("startTimeDailyBookablePeriod" + str(periodNumber)):
                try:
                    cStartTime = datetime.strptime(params.get("startTimeDailyBookablePeriod" + str(periodNumber)), "%H:%M")
                    cEndTime = datetime.strptime(params.get("endTimeDailyBookablePeriod" + str(periodNumber)), "%H:%M")
                    candRoom.addDailyBookablePeriod(cStartTime.strftime("%H:%M"), cEndTime.strftime("%H:%M"))
                except ValueError:
                    continue

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
                if attrName == 'notification email' :
                    candRoom.customAtts['notification email'] = setValidEmailSeparators(v)
                else :
                    candRoom.customAtts[attrName] = v

    # Resv

    def _saveResvCandidateToSession( self, c ):
        if self._formMode == FormMode.MODIF:
            session['rbResvID'] = c.id
            session['rbRoomLocation'] = c.locationName
        session['rbRoomID'] = c.room.id
        session['rbResvCand'] = {
            "startDT": c.startDT,
            "endDT": c.endDT,
            "repeatability": c.repeatability,
            "bookedForId": c.bookedForId,
            "bookedForName": c.bookedForUser.getFullName() if c.bookedForId else c.bookedForName,
            "contactPhone": c.contactPhone,
            "contactEmail": c.contactEmail,
            "reason": c.reason,
            "usesAVC": c.usesAVC,
            "needsAVCSupport": c.needsAVCSupport,
            "needsAssistance": c.needsAssistance,
            "skipConflicting": getattr(self, '_skipConflicting', False),
            "useVC": getattr(c, 'useVC', False)
        }

    def _getErrorsOfResvCandidate(self, c):
        errors = []
        self._thereAreConflicts = False
        if not c.bookedForName and not c.bookedForUser:
            errors.append(_("Booked for can not be blank"))
        if not c.reason:
            errors.append(_("Purpose can not be blank"))
        if not c.isRejected and not c.isCancelled:
            collisions = c.getCollisions(sansID = self._candResv.id)
            if len(collisions) > 0:
                if self._skipConflicting and c.startDT.date() != c.endDT.date():
                    for collision in collisions:
                        c.excludeDay(collision.startDT.date())
                else:
                    self._thereAreConflicts = True
                    errors.append(_("There are conflicts with other bookings"))
            blockedDates = c.getBlockedDates(c.createdByUser())
            if len(blockedDates):
                if self._skipConflicting and c.startDT.date() != c.endDT.date():
                    for blockedDate in blockedDates:
                        c.excludeDay(blockedDate)
                else:
                    self._thereAreConflicts = True
                    errors.append(_("You cannot book this room on this date because the reservations during this \
                                    period have been blocked by somebody else. Please try with another room or date"))
        return errors

    def _loadResvCandidateFromSession(self, candResv, params):
        # After successful searching or failed save
        roomID = params['roomID']
        if isinstance(roomID, list):
            roomID = int(roomID[0])
        else:
            roomID = int(roomID)
        roomLocation = params.get("roomLocation")
        if isinstance(roomLocation, list):
            roomLocation = roomLocation[0]
        if not roomLocation:
            roomLocation = session.get('rbRoomLocation')

        if not candResv:
            candResv = Location.parse( roomLocation ).factory.newReservation() # The same location as for room

        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms(roomID = roomID, location = roomLocation)
        sessionCand = session['rbResvCand']
        candResv.startDT = sessionCand["startDT"]
        candResv.endDT = sessionCand["endDT"]
        candResv.repeatability = sessionCand["repeatability"]
        candResv.bookedForId = sessionCand["bookedForId"]
        candResv.bookedForName = sessionCand["bookedForName"]
        candResv.contactPhone = sessionCand["contactPhone"]
        candResv.contactEmail = setValidEmailSeparators(sessionCand["contactEmail"])
        candResv.reason = sessionCand["reason"]
        candResv.usesAVC = sessionCand["usesAVC"]
        candResv.needsAVCSupport = sessionCand["needsAVCSupport"]
        candResv.needsAssistance = sessionCand["needsAssistance"]
        self._skipConflicting = sessionCand["skipConflicting"]
        candResv.useVC = sessionCand['useVC']
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
        candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )
        self._checkParamsRepeatingPeriod( params )
        candResv.startDT = self._startDT
        candResv.endDT = self._endDT
        candResv.repeatability = self._repeatability
        candResv.bookedForId = params.get("bookedForId")
        candResv.bookedForName = params.get("bookedForName")
        candResv.contactEmail = setValidEmailSeparators(params["contactEmail"])
        candResv.contactPhone = params["contactPhone"]
        candResv.reason = params["reason"]
        candResv.usesAVC = params.get( "usesAVC" ) == "on"
        candResv.needsAVCSupport = params.get( "needsAVCSupport" ) == "on"
        candResv.needsAssistance = params.get( "needsAssistance" ) == "on"
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

    def _loadResvBookingCandidateFromSession( self, params, room ):
        if not params.has_key('roomGUID'):
            raise MaKaCError( _("""The parameter roomGUID is missing."""))
        roomID = int( room.id )
        roomLocation = room.getLocationName()
        candResv = Location.parse( roomLocation ).factory.newReservation() # Create in the same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms( roomID = roomID, location = roomLocation )

        self._checkParamsRepeatingPeriod( params )
        candResv.startDT = self._startDT
        candResv.endDT = self._endDT
        candResv.repeatability = self._repeatability

        return candResv

    def _loadResvCandidateFromDefaults( self, params ):
        # After room details
        if not params.has_key('roomID'):
            raise MaKaCError( _("""The parameter roomID is missing."""))
        if not params.has_key('roomLocation'):
            raise MaKaCError( _("""The parameter roomLocation is missing"""))
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

        # Sets the dates if needed
        dayD = params.get("day")
        monthM = params.get("month")
        yearY = params.get("year")
        dayEnd = params.get("dayEnd")
        monthEnd = params.get("monthEnd")
        yearEnd = params.get("yearEnd")

        hourStart = params.get("hour")
        minuteStart = params.get("minute")
        hourEnd = params.get("hourEnd")
        minuteEnd = params.get("minuteEnd")
        repeatability = params.get("repeatability")

        if hourStart and minuteStart and hourStart.isdigit() and minuteStart.isdigit():
            hourStart = int(hourStart)
            minuteStart = int(minuteStart)
        else:
            hourStart = 8
            minuteStart = 30

        if hourEnd and minuteEnd and hourEnd.isdigit() and minuteEnd.isdigit():
            hourEnd = int(hourEnd)
            minuteEnd = int(minuteEnd)
        else:
            hourEnd = 17
            minuteEnd = 30

        if dayD != None and dayD.isdigit() and \
           monthM != None and monthM.isdigit() and \
           yearY != None and yearY.isdigit():
            candResv.startDT = datetime(int(yearY), int(monthM), int(dayD), hourStart, minuteStart)
            if dayEnd != None and dayEnd.isdigit() and \
               monthEnd != None and monthEnd.isdigit() and \
               yearEnd!= None and yearEnd.isdigit():
                candResv.endDT = datetime(int(yearEnd), int(monthEnd), int(dayEnd), hourEnd, minuteEnd)
                if candResv.endDT.date() != candResv.startDT.date() and candResv.repeatability is None:
                    candResv.repeatability = RepeatabilityEnum.daily
            else:
                candResv.endDT = datetime(int(yearY), int(monthM), int(dayD), hourEnd, minuteEnd)
        else:
            if candResv.startDT == None:
                candResv.startDT = datetime( now.year, now.month, now.day, hourStart, minuteStart )
            if candResv.endDT == None:
                candResv.endDT = datetime( now.year, now.month, now.day, hourEnd, minuteEnd )
        if repeatability is not None:
            if not repeatability.isdigit():
                candResv.repeatability = None
            else:
                candResv.repeatability = int(repeatability)
        if self._getUser():
            if candResv.bookedForUser is None:
                candResv.bookedForUser = self._getUser()
            if candResv.bookedForName == None:
                candResv.bookedForName = self._getUser().getFullName()
            if candResv.contactEmail == None:
                candResv.contactEmail = self._getUser().getEmail()
            if candResv.contactPhone == None:
                candResv.contactPhone = self._getUser().getTelephone()
        else:
            candResv.bookedForUser = None
            candResv.bookedForName = candResv.contactEmail = candResv.contactPhone = ""
        if candResv.reason == None:
            candResv.reason = ""
        if candResv.usesAVC == None:
            candResv.usesAVC = False
        if candResv.needsAVCSupport == None:
            candResv.needsAVCSupport = False
        if candResv.needsAssistance == None:
            candResv.needsAssistance = False

        if not session.get("rbDontAssign") and not params.get("ignoreSession"):
            if session.get("rbDefaultStartDT"):
                candResv.startDT = session.get("rbDefaultStartDT")
            if session.get("rbDefaultEndDT"):
                candResv.endDT = session.get("rbDefaultEndDT")
            if session.get("rbDefaultRepeatability") != None:
                candResv.repeatability = session.get("rbDefaultRepeatability")
            if session.get("rbDefaultBookedForId"):
                candResv.bookedForId = session.get("rbDefaultBookedForId")
            if session.get("rbDefaultBookedForName"):
                candResv.bookedForName = session.get("rbDefaultBookedForName")
            if session.get("rbDefaultReason"):
                candResv.reason = session.get("rbDefaultReason")

            if session.get("rbAssign2Session"):
                locator = locators.WebLocator()
                locator.setSession(session["rbAssign2Session"])
                self._assign2Session = locator.getObject()
            if session.get("rbAssign2Contribution"):
                locator = locators.WebLocator()
                locator.setContribution(session["rbAssign2Contribution"])
                self._assign2Contribution = locator.getObject()

        return candResv


class RHRoomBookingAdminBase( RHRoomBookingBase ):
    """
    Adds admin authorization. All classes that implement admin
    tasks should be derived from this class.
    """
    def _checkProtection( self ):
        if self._getUser() == None:
            self._checkSessionUser()
        elif not self._getUser().isRBAdmin():
            raise MaKaCError( "You are not authorized to take this action." )

class RHRoomBookingWelcome( RHRoomBookingBase ):
    _uh = urlHandlers.UHRoomBookingWelcome

    def _process( self ):
        if Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable():
            self._redirect( urlHandlers.UHRoomBookingMapOfRooms.getURL())
        else:
            self._redirect( urlHandlers.UHRoomBookingBookRoom.getURL())


# 1. Searching

class RHRoomBookingSearch4Rooms( RHRoomBookingBase ):

    def _cleanDefaultsFromSession( self ):
        session.pop("rbDefaultStartDT", None)
        session.pop("rbDefaultEndDT", None)
        session.pop("rbDefaultRepeatability", None)
        session.pop("rbDefaultBookedForId", None)
        session.pop("rbDefaultBookedForName", None)
        session.pop("rbDefaultReason", None)
        session.pop("rbAssign2Session", None)
        session.pop("rbAssign2Contribution", None)

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 8, 30)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 17, 30)

    def _checkParams( self, params ):
        self._cleanDefaultsFromSession()
        self._setGeneralDefaultsInSession()
        self._forNewBooking = False
        self._eventRoomName = None
        if params.get( 'forNewBooking' ):
            self._forNewBooking = params.get( 'forNewBooking' ) == 'True'

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms(allFast = True)
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

class RHRoomBookingBookRoom( RHRoomBookingBase ):

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookRoom( self )
        return p.display()

class RHRoomBookingMapOfRooms(RHRoomBookingBase):

    def _checkParams(self, params):
        RHRoomBookingBase._checkParams(self, params)
        self._roomID = params.get('roomID')

    def _process(self):
        params = {}
        if self._roomID:
            params['roomID'] = self._roomID
        page = roomBooking_wp.WPRoomBookingMapOfRooms(self, **params)
        return page.display()

class RHRoomBookingMapOfRoomsWidget(RHRoomBookingBase):

    def __init__(self, *args, **kwargs):
        RHRoomBookingBase.__init__(self, *args, **kwargs)
        self._cache = GenericCache('MapOfRooms')

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta( 7 - now.weekday() )

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 0, 0)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 0, 0)

    def _checkParams(self, params):
        self._setGeneralDefaultsInSession()
        RHRoomBookingBase._checkParams(self, params)
        self._roomID = params.get('roomID')

    def _businessLogic(self):
        # get all rooms
        defaultLocation = Location.getDefaultLocation()
        rooms = RoomBase.getRooms(location=defaultLocation.friendlyName)
        aspects = [aspect.toDictionary() for aspect in defaultLocation.getAspects()]

        # specialization for a video conference, CERN-specific
        possibleEquipment = defaultLocation.factory.getEquipmentManager().getPossibleEquipment()
        possibleVideoConference = 'Video conference' in possibleEquipment
        self._forVideoConference = possibleVideoConference and self._getRequestParams().get("avc") == 'y'

        # break-down the rooms by buildings
        buildings = {}
        for room in rooms:
            if room.building:

                # if it's the first room in that building, initialize the building
                building = buildings.get(room.building, None)
                if building is None:
                    title = _("Building") + " %s" % room.building
                    building = {'has_coordinates':False, 'number':room.building, 'title':title, 'rooms':[]}
                    buildings[room.building] = building

                # if the room has coordinates, set the building coordinates
                if room.latitude and room.longitude:
                    building['has_coordinates'] = True
                    building['latitude'] = room.latitude
                    building['longitude'] = room.longitude

                # add the room to its building
                if not self._forVideoConference or room.needsAVCSetup:
                    building['rooms'].append(room.fossilize())

        # filter the buildings with rooms and coordinates and return them
        buildings_with_coords = [b for b in buildings.values() if b['rooms'] and b['has_coordinates']]
        self._defaultLocation = defaultLocation.friendlyName
        self._aspects = aspects
        self._buildings = buildings_with_coords

    def _process(self):
        params = dict(self._getRequestParams())
        params["lang"] = session.lang
        params["user"] = session.user.getId()
        key = str(sorted(params.iteritems()))
        html = self._cache.get(key)
        if not html:
            self._businessLogic()
            page = roomBooking_wp.WPRoomBookingMapOfRoomsWidget(self, self._aspects, self._buildings, self._defaultLocation, self._forVideoConference, self._roomID)
            html = page.display()
            self._cache.set(key, html, 300)
        return html

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

        self._includePendingBlockings = False
        if params.get( 'includePendingBlockings' ) == "on": self._includePendingBlockings = True

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
        if self._getUser() and self._getUser().isRBAdmin() and params.get( 'isActive', None ) != "on":
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
        if self._isAutoConfirmed:
            r.resvsNeedConfirmation = False
        for eq in self._equipment:
            r.insertEquipment( eq )

        if self._onlyMy:
            rooms = self._ownedBy.getRooms()
        elif self._availability == "Don't care":
            rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
                                                  freeText=self._freeSearch,
                                                  ownedBy=self._ownedBy,
                                                  roomExample=r,
                                                  pendingBlockings=self._includePendingBlockings,
                                                  onlyPublic=self._isReservable)
            # Special care for capacity (20% => greater than)
            if len (rooms) == 0:
                rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
                                                      freeText=self._freeSearch,
                                                      ownedBy=self._ownedBy,
                                                      roomExample=r,
                                                      minCapacity=True,
                                                      pendingBlockings=self._includePendingBlockings,
                                                      onlyPublic=self._isReservable)
        else:
            # Period specification
            p = ReservationBase()
            p.startDT = self._startDT
            p.endDT = self._endDT
            p.repeatability = self._repeatability
            if self._includePrebookings:
                p.isConfirmed = None   # because it defaults to True

            # Set default values for later booking form
            session["rbDefaultStartDT"] = p.startDT
            session["rbDefaultEndDT"] = p.endDT
            session["rbDefaultRepeatability"] = p.repeatability

            available = ( self._availability == "Available" )

            rooms = CrossLocationQueries.getRooms( \
                location = self._roomLocation,
                freeText = self._freeSearch,
                ownedBy = self._ownedBy,
                roomExample = r,
                resvExample = p,
                available = available,
                pendingBlockings = self._includePendingBlockings )
            # Special care for capacity (20% => greater than)
            if len ( rooms ) == 0:
                rooms = CrossLocationQueries.getRooms( \
                    location = self._roomLocation,
                    freeText = self._freeSearch,
                    ownedBy = self._ownedBy,
                    roomExample = r,
                    resvExample = p,
                    available = available,
                    minCapacity = True,
                    pendingBlockings = self._includePendingBlockings )

        rooms.sort()

        self._rooms = rooms

        self._mapAvailable = Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomList( self, self._onlyMy )
        return p.display()

class RHRoomBookingBookingList( RHRoomBookingBase ):

    def _checkParams( self, params ):
        if params.get('fromSession') == '1':
            params = session.pop('rbBookingListParams', params)
        self._roomGUIDs = []
        self._candResvs = []
        self._allRooms = False
        self._dayLimit = 500
        self._resvLimit = 5000
        roomGUIDs = params.get( "roomGUID" )
        if isinstance( roomGUIDs, list ) and 'allRooms' in roomGUIDs:
            roomGUIDs = 'allRooms'
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

        self._flexibleDatesRange = 0
        flexibleDatesRange = params.get("flexibleDatesRange")
        if flexibleDatesRange and len(flexibleDatesRange.strip()) > 0:
            if flexibleDatesRange == "None":
                self._flexibleDatesRange = 0
            else:
                self._flexibleDatesRange = int(flexibleDatesRange.strip())

        bookedForName = params.get( "bookedForName" )
        if bookedForName and len( bookedForName.strip() ) > 0:
            resvEx.bookedForName = bookedForName.strip()
        reason = params.get( "reason" )
        if reason and len( reason.strip() ) > 0:
            resvEx.reason = reason.strip()
        self._title = "Bookings"

        self._repeatability = None
        repeatability = params.get("repeatability")
        if repeatability and len( repeatability.strip() ) > 0:
            if repeatability == "None":
                self._repeatability = None
                resvEx.repeatability = None
            else:
                self._repeatability = int( repeatability.strip() )
                resvEx.repeatability = int( repeatability.strip() )

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

        self._capacity = None
        capacity = params.get("capacity")
        if capacity and len( capacity.strip() ) > 0:
            self._capacity = int( capacity.strip() )

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

        self._finishDate = False
        finishDate = params.get( "finishDate" )
        if finishDate and len( finishDate.strip() ) > 0:
            if finishDate == 'true':
                self._finishDate = True

        self._newBooking = False
        newBooking = params.get( "newBooking" )
        if newBooking and len( newBooking.strip() ) > 0:
            if newBooking == 'on':
                self._newBooking = True
                self._title = "Select a Room"

        isArchival = params.get( "isArchival" )
        if isArchival and len( isArchival.strip() ) > 0:
            self._isArchival = True
        else:
            self._isArchival = None

        self._autoCriteria = False
        if params.get( "autoCriteria" ) == "True" or not resvEx.startDT:
            now = datetime.now()
            after = now + timedelta( 7 ) # 1 week later

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

        needsAssistance = params.get( "needsAssistance" )
        if needsAssistance and len( needsAssistance.strip() ) > 0:
            resvEx.needsAssistance = needsAssistance == 'on'
        else:
            resvEx.needsAssistance = None

        isHeavy = params.get( "isHeavy" )
        if isHeavy and len( isHeavy.strip() ) > 0:
            self._isHeavy = True
        else:
            self._isHeavy = None

        #self._overload stores type of overload 0 - no overload 1 - too long period selected 2 - too many bookings fetched
        self._overload = 0
        if resvEx.startDT and resvEx.endDT:
            if (resvEx.endDT - resvEx.startDT).days > self._dayLimit:
                self._overload = 1
            elif self._newBooking:
                for rg in self._roomGUIDs:
                    if self._repeatability == 0:
                        self._candResvs.append(self._loadResvBookingCandidateFromSession( params, RoomGUID.parse( rg ).getRoom() ))
                    else:
                        candResv = self._loadResvBookingCandidateFromSession( params, RoomGUID.parse( rg ).getRoom() )
                        candResv.startDT = self._startDT
                        candResv.endDT = self._endDT - timedelta(2 * self._flexibleDatesRange)
                        self._candResvs.append(candResv)
                        for i in range(2 * self._flexibleDatesRange):
                            candResv = self._loadResvBookingCandidateFromSession( params, RoomGUID.parse( rg ).getRoom() )
                            candResv.startDT = self._startDT + timedelta(i + 1)
                            candResv.endDT = self._endDT - timedelta(2 * self._flexibleDatesRange - i - 1)
                            self._candResvs.append(candResv)

        if ((resvEx.endDT - resvEx.startDT).days + 1) * len(self._candResvs) > self._resvLimit:
            self._overload = 2

        self._prebookingsRejected = session.pop('rbPrebookingsRejected', None)
        self._subtitle = session.pop('rbTitle', None)
        self._description = session.pop('rbDescription', None)
        self._resvEx = resvEx
        session['rbBookingListParams'] = params

    def _process( self ):
        # Init
        self._resvs = set()
        self._dayBars = {}

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

        # We only use the cache if no options except a start/end date are sent and all rooms are included
        self._useCache = (self._allRooms and
            not self._onlyPrebookings and
            not self._onlyBookings and
            not self._onlyMy and
            not self._ofMyRooms and
            not self._search and
            not self._isArchival and
            not self._isHeavy and
            not self._resvEx.bookedForName and
            not self._resvEx.reason and
            not self._resvEx.createdBy and
            not self._resvEx.isRejected and
            not self._resvEx.isCancelled and
            not self._resvEx.needsAVCSupport and
            not self._resvEx.usesAVC and
            not self._resvEx.needsAssistance and
            self._resvEx.isConfirmed is None)
        self._cache = None
        self._updateCache = False

        if self._overload != 0:
            p = roomBooking_wp.WPRoomBookingBookingList( self )
            return p.display()

        if self._roomGUIDs:
            rooms = [ RoomGUID.parse( rg ).getRoom() for rg in self._roomGUIDs ]
            if self._rooms is list:
                self._rooms.extend( rooms )
            else:
                self._rooms = rooms

        # Prepare 'days' so .getReservations will use days index
        if not self._resvEx.repeatability:
            self._resvEx.repeatability = RepeatabilityEnum.daily
        periods = self._resvEx.splitToPeriods(endDT = self._resvEx.endDT)
        if self._flexibleDatesRange:
            startDate = self._startDT + timedelta(self._flexibleDatesRange)
            endDate = self._endDT - timedelta(self._flexibleDatesRange)
            for i in range(self._flexibleDatesRange):
                self._resvEx.startDT = startDate - timedelta(i+1)
                self._resvEx.endDT = endDate - timedelta(i+1)
                periods.extend(self._resvEx.splitToPeriods())
                self._resvEx.startDT = startDate + timedelta(i+1)
                self._resvEx.endDT = endDate + timedelta(i+1)
                periods.extend(self._resvEx.splitToPeriods())
            self._resvEx.startDT = self._startDT
            self._resvEx.endDT = self._endDT
        days = [ period.startDT.date() for period in periods ]

        if self._useCache:
            self._cache = GenericCache('RoomBookingCalendar')
            self._dayBars = dict((day, bar) for day, bar in self._cache.get_multi(map(str, days)).iteritems() if bar)
            dayMap = dict(((str(day), day) for day in days))
            for day in self._dayBars.iterkeys():
                days.remove(dayMap[day])
            self._updateCache = bool(len(days))

        day = None # Ugly but...othery way to avoid it?
        for day in days:
            for loc in Location.allLocations:
                self._resvs.update(
                    set(CrossLocationQueries.getReservations(
                        location=loc.friendlyName,
                        resvExample=self._resvEx,
                        rooms=self._rooms,
                        archival=self._isArchival,
                        heavy=self._isHeavy,
                        repeatability=self._repeatability,
                        days=[day])
                    )
                )
            if len(self._resvs) > self._resvLimit:
                self._overload = 2
                break
        if day:
            self._resvEx.endDT = datetime( day.year, day.month, day.day, 23, 59, 00 )

        p = roomBooking_wp.WPRoomBookingBookingList( self )
        return p.display()


# 3. Details of ...

class RHRoomBookingRoomDetails( RHRoomBookingBase ):

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 0, 0)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 0, 0)

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._setGeneralDefaultsInSession()
        self._room = self._target = locator.getObject()

        self._afterActionSucceeded = session.get('rbActionSucceeded')
        self._afterDeletionFailed = session.get('rbDeletionFailed')
        self._formMode = session.get('rbFormMode')

        self._searchingStartDT = self._searchingEndDT = None
        if not params.get('calendarMonths'):
            self._searchingStartDT = session.get("rbDefaultStartDT")
            self._searchingEndDT = session.get("rbDefaultEndDT")

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


class RHRoomBookingBookingDetails(RHRoomBookingBase):

    def _checkParams(self, params):

        locator = locators.WebLocator()
        locator.setRoomBooking(params)
        self._resv = self._target = locator.getObject()
        if not self._resv:
            raise NoReportError("""The specified booking with id "%s" does not exist or has been deleted""" % params["resvID"])
        self._afterActionSucceeded = session.pop('rbActionSucceeded', False)
        self._title = session.pop('rbTitle', None)
        self._description = session.pop('rbDescription', None)
        self._afterDeletionFailed = session.pop('rbDeletionFailed', None)

        self._collisions = []
        if not self._resv.isConfirmed:
            self._resv.isConfirmed = None
            # find pre-booking collisions
            self._collisions = self._resv.getCollisions(sansID=self._resv.id)
            self._resv.isConfirmed = False

        self._clearSessionState()
        self._isAssistenceEmailSetup = getRoomBookingOption('assistanceNotificationEmails')

    def _businessLogic(self):
        pass

    def _process(self):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingDetails(self)
        return p.display()

# 4. New

class RHRoomBookingBookingForm( RHRoomBookingBase ):

    def _checkParams( self, params ):
        self._thereAreConflicts = session.get('rbThereAreConflicts')
        self._skipConflicting = False

        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ) or params.get( "afterCalPreview" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.get('rbCandDataInSession'):
            self._dataFrom = CandidateDataFrom.SESSION

        # Reservation ID?
        resvID = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            resvID = session.get('rbResvID')
            roomLocation = session.get('rbRoomLocation')
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
        self._showErrors = session.get('rbShowErrors')
        if self._showErrors:
            self._errors = session.get('rbErrors')

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

        self._errors = session.get('rbErrors')

        self._candResv = candResv

        if params.get("infoBookingMode"):
            self._infoBookingMode = True
        else:
            self._infoBookingMode = False

        if params.get("skipConflicting"):
            self._skipConflicting = True
        else:
            self._skipConflicting = False

        self._clearSessionState()
        self._requireRealUsers = getRoomBookingOption('bookingsForRealUsers')
        self._isAssistenceEmailSetup = getRoomBookingOption('assistanceNotificationEmails')


    def _checkProtection( self ):

        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
                raise FormValuesError( "You are not authorized to book this room." )

            if not self._candResv.room.canBook( self._getUser() ) and not self._candResv.room.canPrebook( self._getUser() ):
                raise NoReportError( "You are not authorized to book this room." )

            if self._formMode == FormMode.MODIF:
                if not self._candResv.canModify( self.getAW() ):
                    raise MaKaCError( "You are not authorized to take this action." )

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingForm( self )
        return p.display()

class RHRoomBookingCloneBooking( RHRoomBookingBase ):
    """
    Performs open a new booking form with the data of an already existing booking.
    """

    def _checkParams( self, params ):
        # DATA FROM
        session['rbCandDataInSession'] = True

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
    When succeeded redirects to booking details, otherwise returns to booking
    form.
    """

    def _checkParams( self, params ):

        self._roomLocation = params.get("roomLocation")
        self._roomID       = params.get("roomID")
        self._resvID             = params.get( "resvID" )
        if self._resvID == 'None':
            self._resvID = None

        # if the user is not logged in it will be redirected
        # to the login page by the _checkProtection, so we don't
        # need to store info in the session or process the other params
        if not self._getUser():
            return

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
        if self._resvID:
            self._formMode = FormMode.MODIF
            self._resvID = int( self._resvID )
            _candResv = CrossLocationQueries.getReservations( resvID = self._resvID, location = self._roomLocation )
            self._orig_candResv = _candResv

            # Creates a "snapshot" of the reservation's attributes before modification
            self._resvAttrsBefore = self._orig_candResv.createSnapshot()

            import copy
            candResv = copy.copy(_candResv)

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession( candResv, params )
            else:
                self._loadResvCandidateFromParams( candResv, params )

            # Creates a "snapshot" of the reservation's attributes after modification
            self._resvAttrsAfter = candResv.createSnapshot()

        else:
            self._formMode = FormMode.NEW
            candResv = Location.parse( self._roomLocation ).factory.newReservation()
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

        user = self._getUser()
        self._candResv = candResv

        if not (user.isAdmin() or user.isRBAdmin()):
            for nbd in self._candResv.room.getNonBookableDates():
                if nbd.doesPeriodOverlap(self._candResv.startDT, self._candResv.endDT):
                    raise FormValuesError(_("You cannot book this room during the following periods: %s") % ("; ".join(map(lambda x: "from %s to %s"%(x.getStartDate().strftime("%d/%m/%Y (%H:%M)"),x.getEndDate().strftime("%d/%m/%Y (%H:%M)")), self._candResv.room.getNonBookableDates()))))

            if self._candResv.room.getDailyBookablePeriods():
                for nbp in self._candResv.room.getDailyBookablePeriods():
                    if nbp.doesPeriodFit(self._candResv.startDT.time(), self._candResv.endDT.time()):
                        break
                else:
                    raise FormValuesError(_("You must book this room in one of the following time periods: %s") % (", ".join(map(lambda x: "from %s to %s" % (x.getStartTime(), x.getEndTime()), self._candResv.room.getDailyBookablePeriods()))))

        days = self._candResv.room.maxAdvanceDays
        if not (user.isRBAdmin() or user.getId() == self._candResv.room.responsibleId) and days > 0:
            if dateAdvanceAllowed(self._candResv.endDT, days):
                raise FormValuesError(_("You cannot book this room more than %s days in advance.") % days)

        self._params = params
        self._clearSessionState()


    def _checkProtection( self ):
        # If the user is not logged in, we redirect the same reservation page
        if not self._getUser():
            self._redirect(urlHandlers.UHSignIn.getURL(
                                    returnURL = urlHandlers.UHRoomBookingBookingForm.getURL(
                                            roomID = self._roomID,
                                            resvID = self._resvID,
                                            roomLocation = self._roomLocation )))
            self._doProcess = False
        else:
            RHRoomBookingBase._checkProtection(self)
            if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
                raise MaKaCError( "You are not authorized to book this room." )

            if self._formMode == FormMode.MODIF:
                if not self._orig_candResv.canModify( self.getAW() ):
                    raise MaKaCError( "You are not authorized to take this action." )

    def _businessLogic( self ):

        candResv = self._candResv
        emailsToBeSent = []
        self._confirmAdditionFirst = False;

        # Set confirmation status
        candResv.isConfirmed = True
        user = self._getUser()
        if not candResv.room.canBook( user ):
            candResv.isConfirmed = False


        errors = self._getErrorsOfResvCandidate( candResv )

        if not errors and self._answer != 'No':

            isConfirmed = candResv.isConfirmed
            candResv.isConfirmed = None
            # find pre-booking collisions
            self._collisions = candResv.getCollisions(sansID=candResv.id)
            candResv.isConfirmed = isConfirmed

            if not self._forceAddition and self._collisions:
                # save the reservation to the session
                self._saveResvCandidateToSession( candResv )
                # ask for confirmation about the pre-booking
                self._confirmAdditionFirst = True


            # approved pre-booking or booking
            if not self._confirmAdditionFirst:

                # Form is OK and (no conflicts or skip conflicts)
                if self._formMode == FormMode.NEW:
                    candResv.insert()
                    emailsToBeSent += candResv.notifyAboutNewReservation()
                    if candResv.isConfirmed:
                        session['rbTitle'] = _('You have successfully made a booking.')
                        session['rbDescription'] = _('NOTE: Your booking is complete. However, be <b>aware</b> that in special cases the person responsible for a room may reject your booking. In that case you would be instantly notified by e-mail.')
                    else:
                        session['rbTitle'] = _('You have successfully made a <span style="color: Red;">PRE</span>-booking.')
                        session['rbDescription'] = _('NOTE: PRE-bookings are subject to acceptance or rejection. Expect an e-mail with acceptance/rejection information.')
                elif self._formMode == FormMode.MODIF:
                    self._orig_candResv.unindexDayReservations()
                    self._orig_candResv.clearCalendarCache()
                    if self._forceAddition:
                        self._loadResvCandidateFromSession( self._orig_candResv, self._params )
                    else:
                        self._loadResvCandidateFromParams( self._orig_candResv, self._params )
                    self._orig_candResv.update()
                    self._orig_candResv.indexDayReservations()
                    emailsToBeSent += self._orig_candResv.notifyAboutUpdate(self._resvAttrsBefore)

                    # Add entry to the log
                    info = []
                    self._orig_candResv.getResvHistory().getResvModifInfo(info, self._resvAttrsBefore , self._resvAttrsAfter)

                    # If no modification was observed ("Save" was pressed but no field
                    # was changed) no entry is added to the log
                    if len(info) > 1 :
                        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
                        self._orig_candResv.getResvHistory().addHistoryEntry(histEntry)

                    session['rbTitle'] = _('Booking updated.')
                    session['rbDescription'] = _('Please review details below.')

                session['rbActionSucceeded'] = True

                # Booking - reject all colliding PRE-Bookings
                if candResv.isConfirmed and self._collisions:
                    rejectionReason = "Conflict with booking: %s" % urlHandlers.UHRoomBookingBookingDetails.getURL(candResv)
                    for coll in self._collisions:
                        collResv = coll.withReservation
                        if collResv.repeatability is None: # not repeatable -> reject whole booking. easy :)
                            collResv.rejectionReason = rejectionReason
                            collResv.reject()    # Just sets isRejected = True
                            collResv.update()
                            emails = collResv.notifyAboutRejection()
                            emailsToBeSent += emails

                            # Add entry to the booking history
                            info = []
                            info.append("Booking rejected")
                            info.append("Reason: '%s'" % collResv.rejectionReason)
                            histEntry = ResvHistoryEntry(self._getUser(), info, emails)
                            collResv.getResvHistory().addHistoryEntry(histEntry)
                        else: # repeatable -> only reject the specific days
                            rejectDate = coll.startDT.date()
                            collResv.excludeDay(rejectDate, unindex=True)
                            collResv.update()
                            emails = collResv.notifyAboutRejection(date=rejectDate, reason=rejectionReason)
                            emailsToBeSent += emails

                            # Add entry to the booking history
                            info = []
                            info.append("Booking occurence of the %s rejected" % rejectDate.strftime("%d %b %Y"))
                            info.append("Reason: '%s'" % rejectionReason)
                            histEntry = ResvHistoryEntry(self._getUser(), info, emails)
                            collResv.getResvHistory().addHistoryEntry(histEntry)

        else:
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors

            if self._answer == 'No':
                session['rbActionSucceeded'] = True
            else:
                session['rbActionSucceeded'] = False
                session['rbShowErrors'] = True
                session['rbThereAreConflicts'] = self._thereAreConflicts

            self._saveResvCandidateToSession(candResv)

        # Form is not properly filled OR there are conflicts
        self._errors = errors

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

    def _process( self ):

        self._businessLogic()

        if self._errors or self._answer == 'No':
            url = urlHandlers.UHRoomBookingBookingForm.getURL( self._candResv.room, resvID=self._resvID, infoBookingMode=True )
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
        # DATA FROM?
        self._dataFrom = CandidateDataFrom.DEFAULTS
        if params.get( "candDataInParams" ):
            self._dataFrom = CandidateDataFrom.PARAMS
        if session.get('rbCandDataInSession'):
            self._dataFrom = CandidateDataFrom.SESSION

        # Room ID?
        roomID = None
        roomLocation = None
        if self._dataFrom == CandidateDataFrom.SESSION:
            roomID = session.get('rbRoomID')
            roomLocation = session.get('rbRoomLocation')
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
        self._showErrors = session.get('rbShowErrors')
        if self._showErrors:
            self._errors = session.get('rbErrors')

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

        self._errors = session.get('rbErrors')

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
        if (params.get( "largePhotoPath" ) and params.get( "smallPhotoPath" )
            and params["largePhotoPath"].filename and params["smallPhotoPath"].filename):
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

            self._uploadPhotos(candRoom, params)
            session['rbActionSucceeded'] = True
            session['rbFormMode'] = self._formMode
            self._redirect(url) # Redirect to room DETAILS
        else:
            # Failed
            session['rbActionSucceeded'] = False
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors
            session['rbShowErrors'] = True

            self._saveRoomCandidateToSession( candRoom )
            url = urlHandlers.UHRoomBookingRoomForm.getURL(roomLocation=candRoom.locationName)
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
            session['rbTitle'] = _("Room has been deleted.")
            session['rbDescription'] = _("You have successfully deleted the room. All its archival, cancelled and rejected bookings have also been deleted.")
            url = urlHandlers.UHRoomBookingStatement.getURL()
            self._redirect( url ) # Redirect to deletion confirmation
        else:
            # Impossible
            session['rbDeletionFailed'] = True
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
        session['rbTitle'] = _("Booking has been deleted.")
        session['rbDescription'] = _("You have successfully deleted the booking.")
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
        # Only owner (the one who created), the requestor(booked for) and admin can CANCEL
        # (Responsible can not cancel a booking!)
        if not self._resv.canCancel(user):
            raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        # Booking deletion is always possible - just delete
        self._resv.cancel()    # Just sets isCancel = True
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutCancellation()

        # Add entry to the booking history
        info = []
        info.append("Booking cancelled")
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Booking has been cancelled.")
        session['rbDescription'] = _("You have successfully cancelled the booking.")
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
        # Only owner (the one who created), the requestor(booked for) and admin can CANCEL
        # (Owner can not reject his own booking, he should cancel instead)
        if not self._resv.canCancel(user):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._resv.excludeDay( self._date, unindex=True )
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutCancellation( date = self._date )

        # Add entry to the booking history
        info = []
        info.append("Booking occurence of the %s cancelled" %self._date.strftime("%d %b %Y"))
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Selected occurrence has been cancelled.")
        session['rbDescription'] = _("You have successfully cancelled an occurrence of this booking.")
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
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._resv.reject()    # Just sets isRejected = True
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutRejection()

        # Add entry to the booking history
        info = []
        info.append("Booking rejected")
        info.append("Reason : '%s'" %self._resv.rejectionReason)
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Booking has been rejected.")
        session['rbDescription'] = _("NOTE: rejection e-mail has been sent to the user. However, it's advisable to <strong>inform</strong> the user directly. Note that users often don't read e-mails.")
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
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        userRooms = self._getUser().getRooms()
        emailsToBeSent = []

        resvEx = ReservationBase()
        resvEx.isConfirmed = False
        resvEx.isRejected = False
        resvEx.isCancelled = False

        resvs = CrossLocationQueries.getReservations( resvExample = resvEx, rooms = userRooms )

        counter = 0
        for resv in resvs:
            # There's a big difference between 'isConfirmed' being None and False. This value needs to be
            # changed to None and after the search reverted to the previous value. For further information,
            # please take a look at the comment in rb_reservation.py::ReservationBase.getCollisions method
            tmpConfirmed = resv.isConfirmed
            resv.isConfirmed = None
            if resv.getCollisions( sansID = resv.id, boolResult = True ):
                resv.rejectionReason = "Your PRE-booking conflicted with an existing booking. (Please note it IS possible even if you were the first one to PRE-book the room)."
                resv.reject()    # Just sets isRejected = True
                resv.update()
                emailsToBeSent += resv.notifyAboutRejection()
                counter += 1
                # Add entry to the history of the rejected reservation
                info = []
                info.append("Booking rejected due to conflict with existing booking")
                histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
                resv.getResvHistory().addHistoryEntry(histEntry)
            resv.isConfirmed = tmpConfirmed
        session['rbPrebookingsRejected'] = True
        if counter > 0:
            session['rbTitle'] = _("%d conflicting PRE-bookings have been rejected.") % counter
            session['rbDescription'] = _("Rejection e-mails have been sent to the users, with explanation that their PRE-bookings conflicted with the present confirmed bookings.")
        else:
            session['rbTitle'] = _("There are no conflicting PRE-bookings for your rooms.")
            session['rbDescription'] = ""
        for notification in emailsToBeSent:
            GenericMailer.send(notification)
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

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            user = self._getUser()
            # Only responsible and admin can ACCEPT
            if ( not self._resv.room.isOwnedBy( user ) ) and \
                ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        emailsToBeSent = []
        if len( self._resv.getCollisions( sansID = self._resv.id ) ) == 0:
            # No conflicts
            self._resv.isConfirmed = True
            self._resv.update()
            emailsToBeSent += self._resv.notifyAboutConfirmation()

            # Add entry to the booking history
            info = []
            info.append("Booking accepted")
            histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
            self._resv.getResvHistory().addHistoryEntry(histEntry)

            session['rbActionSucceeded'] = True
            session['rbTitle'] = _("Booking has been accepted.")
            session['rbDescription'] = _("NOTE: confirmation e-mail has been sent to the user.")
            url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
            self._redirect( url ) # Redirect to booking details
        else:
            errors = ["PRE-Booking conflicts with other (confirmed) bookings."]
            session['rbActionSucceeded'] = False
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors
            session['rbShowErrors'] = True
            session['rbThereAreConflicts'] = True

            session['rbTitle'] = _("PRE-Booking conflicts with other (confirmed) bookings.")
            session['rbDescription'] = ""

            self._formMode = FormMode.MODIF
            self._saveResvCandidateToSession( self._resv )
            url = urlHandlers.UHRoomBookingBookingForm.getURL( self._resv.room )
            self._redirect( url ) # Redirect to booking details

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

class RHRoomBookingStatement( RHRoomBookingBase ):

    def _checkParams(self, params):
        self._title = session.pop('rbTitle', None)
        self._description = session.pop('rbDescription', None)

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
        if '/' in self._locationName:
            raise FormValuesError(_('Location name may not contain slashes'))
        self._pluginClass = None
        name = params.get("pluginName","default")
        plugs = PluginLoader.getPluginsByType("RoomBooking")
        for plug in plugs:
            if pluginId(plug) == name:
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
            ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process( self ):
        self._resv.excludeDay( self._date, unindex=True )
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutRejection( date = self._date, reason = self._rejectionReason )

        # Add entry to the booking history
        info = []
        info.append("Booking occurence of the %s rejected" %self._date.strftime("%d %b %Y"))
        info.append("Reason : '%s'" %self._rejectionReason)
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Selected occurrence of this booking has been rejected.")
        session['rbDescription'] = _("NOTE: rejection e-mail has been sent to the user.")
        url = urlHandlers.UHRoomBookingBookingDetails.getURL( self._resv )
        self._redirect( url ) # Redirect to booking details


class RHRoomBookingBlockingsForMyRooms(RHRoomBookingBase):

    def _checkParams(self, params):
        self.filterState = params.get('filterState')

    def _process(self):
        activeState = -1
        if self.filterState == 'pending':
            activeState = None
        elif self.filterState == 'accepted':
            activeState = True
        elif self.filterState == 'rejected':
            activeState = False
        myRoomBlocks = defaultdict(list)
        for room in self._getUser().getRooms():
            roomBlocks = RoomBlockingBase.getByRoom(room, activeState)
            if roomBlocks:
                myRoomBlocks[str(room.guid)] += roomBlocks
        p = roomBooking_wp.WPRoomBookingBlockingsForMyRooms(self, myRoomBlocks)
        return p.display()

class RHRoomBookingBlockingDetails(RHRoomBookingBase):

    def _checkParams(self, params):
        blockId = int(params.get('blockingId'))
        self._block = RoomBlockingBase.getById(blockId)
        if not self._block:
            raise MaKaCError('A blocking with this ID does not exist.')

    def _process(self):
        p = roomBooking_wp.WPRoomBookingBlockingDetails(self, self._block)
        return p.display()

class RHRoomBookingBlockingList(RHRoomBookingBase):

    def _checkParams(self, params):
        self.onlyMine = 'onlyMine' in params
        self.onlyRecent = 'onlyRecent' in params
        self.onlyThisYear = 'onlyThisYear' in params

    def _process(self):
        if self.onlyMine:
            blocks = RoomBlockingBase.getByOwner(self._getUser())
            if self.onlyThisYear:
                firstDay = date(date.today().year, 1, 1)
                lastDay = date(date.today().year, 12, 31)
                blocks = [block for block in blocks if block.startDate <= lastDay and firstDay <= block.endDate]
        elif self.onlyThisYear:
            blocks = RoomBlockingBase.getByDateSpan(date(date.today().year, 1, 1), date(date.today().year, 12, 31))
            if self.onlyMine:
                blocks = [block for block in blocks if block.createdByUser == self._getUser()]
        else:
            blocks = RoomBlockingBase.getAll()

        if self.onlyRecent:
            blocks = [block for block in blocks if date.today() <= block.endDate]
        p = roomBooking_wp.WPRoomBookingBlockingList(self, blocks)
        return p.display()


class RHRoomBookingBlockingForm(RHRoomBookingBase):

    def _isOverlapping(self):
        # date overlapping
        for block in RoomBlockingBase.getByDateSpan(self._startDate, self._endDate):
            # check for itself
            if self._block.id != block.id:
                # room overlapping
                if any(block.getBlockedRoom(room) for room in self._blockedRooms):
                    return True
        return False

    def _checkParams(self, params):

        self._action = params.get('action')
        blockId = params.get('blockingId')
        if blockId is not None:
            self._block = RoomBlockingBase.getById(int(blockId))
            if not self._block:
                raise MaKaCError('A blocking with this ID does not exist.')
        else:
            self._block = Factory.newRoomBlocking()()
            self._block.startDate = date.today()
            self._block.endDate = date.today()

        self._errorMessage = ''
        if self._action == 'save':
            from MaKaC.services.interface.rpc import json
            self._reason = params.get('reason', '').strip()
            allowedUsers = json.decode(params.get('allowedUsers', '[]'))
            blockedRoomGuids = json.decode(params.get('blockedRooms', '[]'))
            startDate = params.get('startDate')
            endDate = params.get('endDate')
            if startDate and endDate:
                self._startDate = parseDate(startDate)
                self._endDate = parseDate(endDate)
            else:
                self._startDate = self._endDate = None

            self._blockedRooms = [RoomGUID.parse(guid).getRoom() for guid in blockedRoomGuids]
            self._allowedUsers = [RoomBlockingPrincipal.getByTypeId(fossil['_type'], fossil['id']) for fossil in allowedUsers]

            if not self._reason or not self._blockedRooms:
                self._errorMessage = _('Please check blocked rooms and reason for blocking.')
            elif self._createNew and (not self._startDate or not self._endDate or self._startDate > self._endDate):
                self._errorMessage = _('Please check your blocking dates.')
            elif self._isOverlapping():
                self._errorMessage = _('Your blocking is overlapping with other blockings.')

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._doProcess: # if we are not logged in
            return
        if not self._createNew:
            if not self._block.canModify(self._getUser()):
                raise MaKaCError("You are not authorized to modify this blocking.")
        else:
            if not (Room.isAvatarResponsibleForRooms(self._getUser()) or self._getUser().isAdmin() or self._getUser().isRBAdmin()):
                raise MaKaCError("Only users who own at least one room are allowed to create blockings.")

    def _process(self):
        if self._action == 'save' and not self._errorMessage:
            self._block.message = self._reason
            if self._createNew:
                self._block.createdByUser = self._getUser()
                self._block.startDate = self._startDate
                self._block.endDate = self._endDate
            currentBlockedRooms = set()
            for room in self._blockedRooms:
                br = self._block.getBlockedRoom(room)
                if not br:
                    br = BlockedRoom(room)
                    self._block.addBlockedRoom(br)
                    if room.getResponsible() == self._getUser():
                        br.approve(sendNotification=False)
                currentBlockedRooms.add(br)
            # Remove blocked rooms which have been removed from the list
            for br in set(self._block.blockedRooms) - currentBlockedRooms:
                self._block.delBlockedRoom(br)
            # Replace allowed-users/groups list
            self._block.allowed = self._allowedUsers
            # Insert/update(re-index) the blocking
            if self._createNew:
                self._block.insert()
            else:
                self._block.update()
            self._redirect(urlHandlers.UHRoomBookingBlockingsBlockingDetails.getURL(self._block))

        elif self._action == 'save' and self._createNew and self._errorMessage:
            # If we are creating a new blocking and there are errors, populate the block object anyway to preserve the entered values
            self._block.message = self._reason
            self._block.startDate = self._startDate
            self._block.endDate = self._endDate
            self._block.allowed = self._allowedUsers
            for room in self._blockedRooms:
                self._block.addBlockedRoom(BlockedRoom(room))

        p = roomBooking_wp.WPRoomBookingBlockingForm(self, self._block, self._errorMessage)
        return p.display()

    @property
    def _createNew(self):
        return self._block.id is None

class RHRoomBookingDelete(RHRoomBookingBase):

    def _checkParams(self, params):
        blockId = int(params.get('blockingId'))
        self._block = RoomBlockingBase.getById(blockId)

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        if not self._block.canDelete(self._getUser()):
            raise MaKaCError("You are not authorized to delete this blocking.")

    def _process(self):
        self._block.remove()
        self._redirect(urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=True, onlyRecent=True))
