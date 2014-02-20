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

from datetime import datetime, timedelta

from flask import flash, request, session

from indico.core.errors import IndicoError, FormValuesError, NoReportError
from indico.util.i18n import _

from .. import RHRoomBookingBase
from ...models.reservations import Reservation
from ...models.rooms import Room
from ...models.utils import sifu
from ...views.user import reservations as reservation_views
from ..forms import BookingForm, BookingListForm


class RHRoomBookingBookRoom(RHRoomBookingBase):

    def _process(self):
        self._rooms, self._max_capacity = Room.getRoomsWithMaxCapacity()
        return reservation_views.WPRoomBookingBookRoom(self).display()


class RHRoomBookingBookingDetails(RHRoomBookingBase):

    def _checkParams(self):
        resv_id = request.view_args.get('resvID')
        self._reservation = Reservation.getById(request.view_args.get('resvID'))
        if not self._reservation:
            raise IndicoError('No booking with id: {}'.format(resv_id))

    def _process(self):
        return reservation_views.WPRoomBookingBookingDetails(self).display()


class RHRoomBookingBookingList(RHRoomBookingBase):

    def __getTitle(self):
        return {
                (True, False, False, False, False): _('Select a Room'),
                (False, False, False, False, False): _('Bookings'),
                (False, True, False, False, False): _('PRE-Bookings'),
                (False, False, True, False, False): _('My Bookings'),
                (False, True, True, False, False): _('My PRE-Bookings'),
                (False, False, False, True, False): _('Bookings for my rooms'),
                (False, True, False, True, False): _('Pre-Bookings for my rooms'),
                (False, False, True, True, False): _('My Bookings for my rooms'),
                (False, True, True, True, False): _('My Pre-Bookings for my rooms'),
                (False, False, True, True, True): _('Search My Bookings for my rooms'),
                (False, True, True, True, True): _('Search My Pre-Bookings for my rooms'),
                (False, False, True, False, True): _('Search My Bookings'),
                (False, True, True, False, True): _('Search My Pre-Bookings'),
                (False, False, False, True, True): _('Search Bookings for my rooms'),
                (False, True, False, True, True): _('Search Pre-Bookings for my rooms'),
                (False, False, False, False, True): _('Search Bookings'),
                (False, True, False, False, True): _('Search Pre-Bookings'),
            }.get(
                (
                    self._form.is_new_booking.data,
                    self._form.is_only_pre_bookings.data,
                    self._form.is_only_mine.data,
                    self._form.is_only_my_rooms.data,
                    self._form.is_search.data
                ),
                _('{} Booking(s) found').format(self._reservation_count)
            )

    def _checkParams(self):
        self._form = BookingListForm(request.values)

    def _process(self):
        if self._form.validate():
            if self._form.is_search.data:
                self._reservations = Room.getFilteredReservationsInSpecifiedRooms(
                    self._form,
                    self._getUser()
                )
                print 'SEARCH =================================='
            else:
                self._reservations = Room.getReservationsForAvailability(
                    self._form.start_date.data,
                    self._form.end_date.data,
                    self._form.room_id_list.data
                )
                print 'NEW BOOKING ========================='
            self._reservation_count = len(self._reservations)
        else:
            # TODO: actually this case shouldn't happen
            self._reservations = []
            self._reservation_count = 0
        self._title = self.__getTitle()
        return reservation_views.WPRoomBookingBookingList(self).display()


class RHRoomBookingBookingForm(RHRoomBookingBase):

    def _checkParams(self):
        self._form = BookingForm()
        if self._form.is_submitted():
            if 'resvID' in request.view_args:  # modification
                if self._form.validate_on_submit():
                    self._reservation = Reservation()
                    self._form.populate_obj(self._reservation)
                else:
                    pass

        # self._requireRealUsers = getRoomBookingOption('bookingsForRealUsers')
        # self._isAssistenceEmailSetup = getRoomBookingOption('assistanceNotificationEmails')

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # if self._doProcess:
        #     if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
        #         raise FormValuesError('You are not authorized to book this room.')

        #     if not self._candResv.room.canBook(self._getUser()) and not self._candResv.room.canPrebook(self._getUser()):
        #         raise NoReportError('You are not authorized to book this room.')

        #     if self._formMode == FormMode.MODIF:
        #         if not self._candResv.canModify(self.getAW()):
        #             raise IndicoError('You are not authorized to take this action.')

    def _process(self):
        self._rooms = Room.getRooms()
        return reservation_views.WPRoomBookingBookingForm(self).display()


class RHRoomBookingSaveBooking(RHRoomBookingBase):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to booking details, otherwise returns to booking
    form.
    """

    def _checkParams( self, params ):

        self._roomLocation = params.get("roomLocation")
        self._roomID = params.get("roomID")
        self._resvID = params.get( "resvID" )
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


class RHRoomBookingStatement(RHRoomBookingBase):

    def _checkParams(self):
        self._title = session.pop('rbTitle', None)
        self._description = session.pop('rbDescription', None)

    def _process(self):
        return reservation_views.WPRoomBookingStatement(self).display()


class RHRoomBookingAcceptBooking(RHRoomBookingBase):

    def _checkParams(self):
        resvID = int( params.get( "resvID" ) )
        roomLocation = params.get( "roomLocation" )
        self._resv = CrossLocationQueries.getReservations( resvID = resvID, location = roomLocation )
        self._target = self._resv

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            user = self._getUser()
            # Only responsible and admin can ACCEPT
            if ( not self._resv.room.isOwnedBy( user ) ) and \
                ( not self._getUser().isRBAdmin() ):
                raise MaKaCError( "You are not authorized to take this action." )

    def _process(self):
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


class RHRoomBookingCancelBooking(RHRoomBookingBase):

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


class RHRoomBookingSearch4Bookings(RHRoomBookingBase):

    def _process(self):
        self._rooms = Room.getRooms()
        return reservation_views.WPRoomBookingSearch4Bookings(self).display()
