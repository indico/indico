# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from flask import request, session

from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.rh.base import RHProtected

from indico.core.errors import AccessError

from .mixins import RoomBookingAvailabilityParamsMixin
from .utils import rb_check_user_access, FormMode


class RHRoomBookingProtected(RHProtected):

    def _checkSessionUser(self):
        user = self._getUser()
        if user:
            try:
                if PluginsHolder().getPluginType('RoomBooking').isActive():
                    if not rb_check_user_access(user):
                        raise AccessError()
            except KeyError:
                pass
        else:
            self._redirect(self._getLoginURL())
            self._doProcess = False


class RHRoomBookingBase(RoomBookingAvailabilityParamsMixin, RHRoomBookingProtected):
    """
    All room booking related handlers are derived from this class.
    This gives them:
    - several general use methods
    - login-protection
    - auto connecting/disconnecting from room booking db
    """

    def _checkProtection(self):
        RHRoomBookingProtected._checkProtection(self)

    # TODO: naming of variables
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

    def _saveRoomCandidateToSession(self, room):
        if self._formMode == FormMode.MODIF:
            session['rbRoomID'] = room.id
        session['rbRoomCand'] = room

    def _getErrorsOfRoomCandidate(self, room):
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
            if c.longitude and float(c.longitude) < 0:
                errors.append("Longitude must be a positive number")
        except ValueError:
            errors.append("Longitude must be a number")

        try:
            if c.latitude and float(c.latitude) < 0:
                errors.append("Latitude must be a positive number")
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

    # TODO: check because this should be handled by sqlalchemy
    def _loadRoomCandidateFromDefaults(self, candRoom):
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
            collisions = c.getCollisions(sansID=self._candResv.id)
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
                    errors.append(_("You cannot book this room on this date "
                                    "because the reservations during this period "
                                    "have been blocked by somebody else. "
                                    "Please try with another room or date"))
        return errors

    def _loadResvCandidateFromSession( self, candResv, params ):
        # After successful searching or failed save
        roomID = params['roomID']
        if isinstance( roomID, list ):
            roomID = int( roomID[0] )
        else:
            roomID = int( roomID )
        roomLocation = params.get( "roomLocation" )
        if isinstance( roomLocation, list ):
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
