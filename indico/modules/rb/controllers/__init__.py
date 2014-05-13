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

from datetime import datetime
from flask import session

from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.rh.base import RHProtected
from indico.core.errors import AccessError
from indico.util.i18n import _
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


    # Resv

    def _check_start(self, default=None):
        if default is None:
            default = datetime.now()

        sdate = request.values.get('sdate', '')
        stime = request.values.get('stime', '')

        try:
            sdate = datetime.strptime(sdate, '%Y-%m-%d').date()
        except ValueError:
            sdate = default.date()

        try:
            stime = datetime.strptime(stime, '%H:%M').time()
        except ValueError:
            stime = default.time()

        self.start = datetime.combine(sdate, stime)


    def _check_end(self, default=None):
        if default is None:
            default = datetime.now()

        edate = request.values.get('edate', '')
        etime = request.values.get('etime', '')

        try:
            edate = datetime.strptime(edate, '%Y-%m-%d').date()
        except ValueError:
            edate = default.date()

        try:
            etime = datetime.strptime(etime, '%H:%M').time()
        except ValueError:
            etime = default.time()

        self.end = datetime.combine(edate, etime)

    def _checkAndSetParamsForReservation(self):
        pass

    def _saveResvCandidateToSession(self, c):
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
            candResv = Location.parse(roomLocation).factory.newReservation()  # The same location as for room

        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms(roomID=roomID, location=roomLocation)
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

    def _loadResvCandidateFromParams(self, candResv, params):
        # After calendar preview
        roomID = params['roomID']
        if isinstance(roomID, list):
            roomID = int(roomID[0])
        else:
            roomID = int(roomID)
        roomLocation = params.get("roomLocation")
        if isinstance(roomLocation, list):
            roomLocation = roomLocation[0]
        if not candResv:
            candResv = Location.parse(roomLocation).factory.newReservation()  # The same location as room
        candResv.room = CrossLocationQueries.getRooms(roomID=roomID, location=roomLocation)
        self._checkParamsRepeatingPeriod(params)
        candResv.startDT = self._startDT
        candResv.endDT = self._endDT
        candResv.repeatability = self._repeatability
        candResv.bookedForId = params.get("bookedForId")
        candResv.bookedForName = params.get("bookedForName")
        candResv.contactEmail = setValidEmailSeparators(params["contactEmail"])
        candResv.contactPhone = params["contactPhone"]
        candResv.reason = params["reason"]
        candResv.usesAVC = params.get("usesAVC") == "on"
        candResv.needsAVCSupport = params.get("needsAVCSupport") == "on"
        candResv.needsAssistance = params.get("needsAssistance") == "on"
        self._skipConflicting = params.get("skipConflicting") == "on"
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

    def _loadResvBookingCandidateFromSession(self, params, room):
        if 'roomGUID' not in params:
            raise MaKaCError(_("""The parameter roomGUID is missing."""))
        roomID = int(room.id)
        roomLocation = room.getLocationName()
        candResv = Location.parse(roomLocation).factory.newReservation()  # Create in the same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms(roomID=roomID, location=roomLocation)

        self._checkParamsRepeatingPeriod(params)
        candResv.startDT = self._startDT
        candResv.endDT = self._endDT
        candResv.repeatability = self._repeatability

        return candResv

    def _loadResvCandidateFromDefaults(self, params):
        # After room details
        if 'roomID' not in params:
            raise MaKaCError(_("""The parameter roomID is missing."""))
        if 'roomLocation' not in params:
            raise MaKaCError(_("""The parameter roomLocation is missing"""))
        roomID = int(params['roomID'])
        roomLocation = params['roomLocation']
        candResv = Location.parse(roomLocation).factory.newReservation()  # Create in the same location as room
        if not candResv.room:
            candResv.room = CrossLocationQueries.getRooms(roomID=roomID, location=roomLocation)
        # Generic defaults
        now = datetime.now()
        if now.weekday() in [4, 5]:
            now = now + timedelta(7 - now.weekday())
        else:
            now = now + timedelta(1)

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

        if (dayD is not None and dayD.isdigit() and monthM is not None and monthM.isdigit() and yearY is not None
                and yearY.isdigit()):
            candResv.startDT = datetime(int(yearY), int(monthM), int(dayD), hourStart, minuteStart)
            if (dayEnd is not None and dayEnd.isdigit() and monthEnd is not None and monthEnd.isdigit()
                    and yearEnd is not None and yearEnd.isdigit()):
                candResv.endDT = datetime(int(yearEnd), int(monthEnd), int(dayEnd), hourEnd, minuteEnd)
                if candResv.endDT.date() != candResv.startDT.date() and candResv.repeatability is None:
                    candResv.repeatability = RepeatabilityEnum.daily
            else:
                candResv.endDT = datetime(int(yearY), int(monthM), int(dayD), hourEnd, minuteEnd)
        else:
            if candResv.startDT is None:
                candResv.startDT = datetime(now.year, now.month, now.day, hourStart, minuteStart)
            if candResv.endDT is None:
                candResv.endDT = datetime(now.year, now.month, now.day, hourEnd, minuteEnd)
        if repeatability is not None:
            if not repeatability.isdigit():
                candResv.repeatability = None
            else:
                candResv.repeatability = int(repeatability)
        if self._getUser():
            if candResv.bookedForUser is None:
                candResv.bookedForUser = self._getUser()
            if candResv.bookedForName is None:
                candResv.bookedForName = self._getUser().getFullName()
            if candResv.contactEmail is None:
                candResv.contactEmail = self._getUser().getEmail()
            if candResv.contactPhone is None:
                candResv.contactPhone = self._getUser().getTelephone()
        else:
            candResv.bookedForUser = None
            candResv.bookedForName = candResv.contactEmail = candResv.contactPhone = ""
        if candResv.reason is None:
            candResv.reason = ""
        if candResv.usesAVC is None:
            candResv.usesAVC = False
        if candResv.needsAVCSupport is None:
            candResv.needsAVCSupport = False
        if candResv.needsAssistance is None:
            candResv.needsAssistance = False

        if not session.get("rbDontAssign") and not params.get("ignoreSession"):
            if session.get("rbDefaultStartDT"):
                candResv.startDT = session.get("rbDefaultStartDT")
            if session.get("rbDefaultEndDT"):
                candResv.endDT = session.get("rbDefaultEndDT")
            if session.get("rbDefaultRepeatability") is not None:
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
