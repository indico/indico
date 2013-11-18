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

from indico.modules.rb.controllers import RHRoomBookingBase


class RHRoomBookingBookRoom( RHRoomBookingBase ):

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookRoom( self )
        return p.display()


class RHRoomBookingBookingDetails( RHRoomBookingBase ):

    def _checkParams( self, params ):

        locator = locators.WebLocator()
        locator.setRoomBooking( params )
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

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingBookingDetails( self )
        return p.display()


class RHRoomBookingBookingList( RHRoomBookingBase ):

    def _checkParams( self, params ):
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

    def _process( self ):
        # Init
        self._resvs = []
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
                self._resvs += CrossLocationQueries.getReservations( location = loc.friendlyName, resvExample = self._resvEx, rooms = self._rooms, archival = self._isArchival, heavy = self._isHeavy, repeatability=self._repeatability,  days = [day] )
            if len(self._resvs) > self._resvLimit:
                self._overload = 2
                break
        if day:
            self._resvEx.endDT = datetime( day.year, day.month, day.day, 23, 59, 00 )

        p = roomBooking_wp.WPRoomBookingBookingList( self )
        return p.display()


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


class RHRoomBookingStatement( RHRoomBookingBase ):

    def _checkParams(self, params):
        self._title = session.pop('rbTitle', None)
        self._description = session.pop('rbDescription', None)

    def _process( self ):
        return roomBooking_wp.WPRoomBookingStatement( self ).display()


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
                resv.rejectionReason = "Your PRE-booking conflicted with exiting booking. (Please note it IS possible even if you were the first one to PRE-book the room)."
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


class RHRoomBookingSearch4Bookings( RHRoomBookingBase ):

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms( allFast = True )
        self._rooms.sort()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingSearch4Bookings( self )
        return p.display()
