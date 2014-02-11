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

from flask import request, session

from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.rh.base import RHProtected

from indico.core.db import db
from indico.core.errors import AccessError
from indico.util.i18n import _

from .mixins import RoomBookingAvailabilityParamsMixin
from .utils import rb_check_user_access, FormMode
from ..models.rooms import Room
from ..models.room_bookable_times import BookableTime
from ..models.room_nonbookable_dates import NonBookableDate


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

    # Room

    def _checkAndSetParams(self):
        errors, c, f = [], self._room, request.form

        def testAndSet(ls):
            for l in ls:
                p, e, extra, t = l + [None]*(4 - len(l))
                v = f.get(p)
                setattr(self._room, p, v)
                try:
                    if t:
                        v = t(v)
                        setattr(self._room, p, v)
                    if extra and not extra(v):
                        raise RuntimeError
                except Exception:
                    errors.append(e)

        not_empty, positive, on, empty_or_int, empty_or_positive = (
            lambda e: e != '',
            lambda e: e > 0,
            lambda e: e == 'on',
            lambda e: int(e) if e else 0,
            lambda e: True if e == '' else float(e) > 0
        )
        testAndSet([
            ['name'],
            ['floor', _('Floor can not be blank'), not_empty],
            ['number', _('Room number can not be blank'), not_empty],
            ['building', _('Building can not be blank'), not_empty],
            ['owner_id', _('Room must have a responsible person'), not_empty],
            ['capacity', _('Capacity must be a positive integer'), positive, int],
            ['longitude', _('Longitude must be a positive number'), empty_or_positive],
            ['latitude', _('Latitude must be a positive number'), empty_or_positive],
            ['notification_for_start', _('Notification for start'
             ' must be nonnegative number. Put zero to cancel.'), lambda e: e >= 0, int],
            ['max_advance_days', _('Maximum days before a'
             ' reservation must be a positive number'), positive, int],
            ['surface_area', _('Surface area must be a positive number'), lambda e: e >= 0, empty_or_int],
            ['is_active', '', None, on],
            ['is_reservable', '', None, on],
            ['notification_for_end', '', None, on],
            ['reservations_need_confirmation', '', None, on],
            ['notification_for_responsible', '', None, on],
            ['notification_for_assistance', '', None, on],
            ['comments']
        ])

        # set name: building-floor-name
        self._room.updateName()

        # bookable-times
        self._bookable_times, bookable_times_count = [], f.get('dailyBookablePeriodCounter', type=int)
        exist_error, format_error, valid_error = False, False, False
        for i in xrange(bookable_times_count):
            try:
                s, e = f.get('startTimeDailyBookablePeriod{}'.format(i)), f.get('endTimeDailyBookablePeriod{}'.format(i))
                if s and e:
                    start_time = datetime.strptime(s, '%H:%M').time()
                    end_time = datetime.strptime(e, '%H:%M').time()
                    if start_time < end_time:
                        self._bookable_times.append(BookableTime(start_time=start_time, end_time=end_time))
                    else:
                        valid_error = True
                elif s + e:
                    exist_error = True
            except ValueError:
                format_error = True

        if exist_error:
            errors.append(_('Daily availability periods must have start and end.'))

        if format_error:
            errors.append(_('Daily availability periods must be '
                            'in correct time format \'HH:MM\''))

        if valid_error:
            errors.append(_('Period start time should come before end time '
                            'in daily availability period field'))

        # nonbookable_dates
        self._nonbookable_dates, nonbookable_dates_count = [], f.get('nonBookablePeriodCounter', type=int)
        exist_error, format_error, valid_error = False, False, False
        for i in xrange(nonbookable_dates_count):
            try:
                s, e = f.get('startDateNonBookablePeriod{}'.format(i)), f.get('endDateNonBookablePeriod{}'.format(i))
                if s and e:
                    st, et = datetime.strptime(s, '%d/%m/%Y %H:%M'), datetime.strptime(e, '%d/%m/%Y %H:%M')
                    if st < et:
                        self._nonbookable_dates.append(NonBookableDate(start_date=st, end_date=et))
                    else:
                        valid_error = True
                elif s + e:
                    exist_error = True
            except ValueError:
                format_error = True

        if exist_error:
            errors.append(_('Unavailable dates must have start and end.'))
        if format_error:
            errors.append(_('Unavailable dates must be in the form of \'DD/MM/YYYY HH:MM\''))
        if valid_error:
            errors.append(_('End must be later than start date in unavailable dates'))

        self._equipments = []
        for eq in self._location.getEquipments():
            if f.get('equ_{}'.format(eq.name), None) == 'on':
                self._equipments.append(eq)

        if not self._bookable_times and errors:
            self._bookable_times.append(BookableTime(start_time=None, end_time=None))
            self._nonbookable_dates.append(NonBookableDate(start_date=None, end_date=None))

        # if (request.files.get('largePhotoPath') != '') ^ (request.files.get('smallPhotoPath') != ''):
        #     errors.append(_('Either upload both photos or none'))

        # Custom attributes
        # for attr in self._location.getAttributes():
        #     if attr['name'] == 'notification email':
        #         if c.customAtts['notification email'] and not validMail(c.customAtts['notification email']):
        #             errors.append(_('Invalid format for the notification email'))
        #     if attr['required']:
        #         if attr['name'] not in c.customAtts and c.customAtts[attr['name']]:
        #             errors.append(_('{0} can not be blank'.format(attr['name']))

        return errors

    # Resv

    def _checkAndSetParamsForReservation(self):
        pass

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
