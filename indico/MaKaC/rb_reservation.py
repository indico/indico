# -*- coding: utf-8 -*-
##
## $Id: rb_reservation.py,v 1.14 2009/05/14 18:05:51 jose Exp $
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

"""
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""

from datetime import datetime, timedelta, date
from MaKaC.rb_tools import iterdays, weekNumber, doesPeriodsOverlap, overlap, Period, Impersistant, checkPresence, fromUTC, toUTC, formatDateTime, formatDate
from MaKaC.rb_location import ReservationGUID, Location, CrossLocationQueries
from MaKaC.accessControl import AccessWrapper
from MaKaC.user import AvatarHolder, Avatar
from MaKaC.common.Configuration import Config
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.conference import ConferenceHolder

class RepeatabilityEnum( object ):
    """
    Enumeration - types of repetition.
    """
    daily, onceAWeek, onceEvery2Weeks, onceEvery3Weeks, onceAMonth = range( 5 )
    # How many days are between consequent repeatings
    rep2diff = {
        daily: 1,
        onceAWeek: 7,
        onceEvery2Weeks: 14,
        onceEvery3Weeks: 21
    }

    rep2description = {
        None: "Single day",
        daily: "Daily",
        onceAWeek: "Once a week",
        onceEvery2Weeks: "Once every 2 weeks",
        onceEvery3Weeks: "Once every 3 weeks",
        onceAMonth: "Once a month",
    }

class WeekDayEnum( object ):
    """
    Enumeration - days of the week.
    """
    monday, tuesday, wednesday, thursday, friday, saturday, sunday = range( 7 )

    week2desc = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday' ]

# This text prepends every notification - in general it should be empty
TEST_VERSION_WARNING = "" #"[This notification considers FAKE event in TEST version of new Indico::CRBS. You can ignore it.]"

# Room booking module notifications will be send to this e-mail when debug is on
EMAIL_FOR_DEBUG_NOTIFICATIONS = "jose.benito.gonzalez@cern.ch"
EMAIL_FROM_PREFIX = "noreply-"

# Room booking module notifications will be send to this e-mail when debug is on
NOTIFICATION_SUBJECT_PREFIX = "[CRBS] "

# Carbon copy of ALL room booking notifications will be send to this email
EMAIL_FOR_CATCH_ALL_NOTIFICATIONS = ""

class ReservationBase( object ):
    """
    Generic reservation, Data Access Layer independant.
    Represents physical room reservation.
    """

    # !=> Properties are in the end of class definition

    # Management -------------------------------------------------------------

    def __init__( self ):
        """
        Do NOT insert object into database in the constructor.
        """
        pass

    def insert( self ):
        """
        Inserts reservation into database (SQL: INSERT).
        """
        if self.isCancelled == None: self.isCancelled = False
        if self.isRejected == None: self.isRejected = False
        if self.startDT.date() == self.endDT.date():
            self.repeatability = None
        self.checkIntegrity()

    def update( self ):
        """
        Updates reservation in database (SQL: UPDATE)
        """
        if self.startDT.date() == self.endDT.date():
            self.repeatability = None
        self.checkIntegrity()

    def remove( self ):
        """
        Removes reservation from database (SQL: DELETE)
        """
        pass

    def cancel( self ):
        """
        FINAL (not intented to be overriden)
        When user cancels reservation.
        """
        self.isCancelled = True

    def reject( self ):
        """
        FINAL (not intented to be overriden)
        When responsible rejects reservation.
        """
        self.isRejected = True

    # Notifications ----------------------------------------------------------

    def notifyAboutNewReservation( self ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) user and responsible about creation of a new reservation.
        Called after insert().
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []
        # ---- Email creator and contact ----
        if self.createdByUser(): # Imported bookings does not have creator
            to = self.createdByUser().getEmail()
            to2 = ""
            if self.contactEmail != None and self.contactEmail != "":
                to2 = self.contactEmail
            if self.isConfirmed:
                subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] You have made a New Booking on " + formatDateTime(self.startDT)
                wc = WTemplated( 'RoomBookingEmail_2UserAfterBookingInsertion' )
            else:
                subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Your PRE-Booking waits for Acceptance"
                wc = WTemplated( 'RoomBookingEmail_2UserAfterPreBookingInsertion' )
            text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self } )
            fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            addrs = []
            if debug:
                addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
            else:
                addrs.append( to )
                if to2 != "" and to != to2:
                    addrs.append( to2 )
                if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                    addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
            emails.append(maildata)

        # ---- Email responsible(s) ----

        toMain = self.room.getResponsible().getEmail()

        if self.isConfirmed:
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] New Booking on " + formatDateTime(self.startDT)
            bookingMessage = "Book"
        else:
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] New PRE-Booking on " + formatDateTime(self.startDT)
            bookingMessage = "PRE-book"
        wc = WTemplated( 'RoomBookingEmail_2ResponsibleAfterBookingInsertion' )
        text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self, 'bookingMessage': bookingMessage } )

        fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
        addrs = []
        if debug:
            addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
        else:
            addrs.append( toMain )
            if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            if self.room.customAtts.get( 'notification email', None ):
                addrs.append(self.room.customAtts.get( 'notification email' ).strip())
        maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
        emails.append(maildata)

        # ---- Email AVC Support ----

        if self.isConfirmed  and  self.usesAVC: # Inform only about confirmed bookings
            to = Location.parse( self.locationName ).getAVCSupportEmails()
            if to:
                subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] New Booking on " + formatDateTime(self.startDT)
                wc = WTemplated( 'RoomBookingEmail_2AVCSupportAfterBookingInsertion' )
                text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation': self } )
                fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
                addrs = []
                if debug:
                    addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
                else:
                    addrs += to
                    if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                        addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
                maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
                emails.append(maildata)
        return emails

    def notifyAboutCancellation( self, date = None ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) user and responsible about reservation cancellation.
        Called after cancel().
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []

        if date:
            occurrenceText = " (SINGLE OCCURRENCE)"
            startDate = formatDate(date)
        else:
            occurrenceText = ""
            # Fix by David: include date in this mails too. I have put a try...except in case the date is not accessible in this method
            try:
                startDate = formatDateTime(self.startDT)
            except:
                startDate = ""

        # ---- Email user ----

        if self.createdByUser(): # Imported bookings does not have creator
            to = self.createdByUser().getEmail()
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Cancellation Confirmation on " + startDate + " %s" % occurrenceText
            wc = WTemplated( 'RoomBookingEmail_2UserAfterBookingCancellation' )
            text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self, 'date':date } )
            fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            addrs = []
            if debug:
                addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
            else:
                addrs.append( to )
                if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                    addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
            emails.append(maildata)

        # ---- Email responsible ----

        toMain = self.room.getResponsible().getEmail()

        subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Cancelled Booking on " + startDate + " %s" % occurrenceText
        wc = WTemplated( 'RoomBookingEmail_2ResponsibleAfterBookingCancellation' )
        text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self, 'date':date } )
        fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
        addrs = []
        if debug:
            addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
        else:
            addrs.append( toMain )
            if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            if self.room.customAtts.get( 'notification email', None ):
                addrs.append(self.room.customAtts.get( 'notification email' ).strip())
        maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
        emails.append(maildata)

        # ---- Email AVC Support ----

        if self.isCancelled and self.isConfirmed  and  self.usesAVC: # Inform only about confirmed bookings
            to = Location.parse( self.locationName ).getAVCSupportEmails()
            if to:
                subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Booking Cancelled on " + startDate
                wc = WTemplated( 'RoomBookingEmail_2AVCSupportAfterBookingCancellation' )
                text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation': self } )
                fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
                addrs = []
                if debug:
                    addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
                else:
                    addrs += to
                    if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                        addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
                maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
                emails.append(maildata)
        return emails

    def notifyAboutRejection( self, date = None, reason = None ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) user and responsible about reservation rejection.
        Called after reject().
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []
        reason = self.rejectionReason or reason

        # Fix by David: include date in this mails too. I have put a try...except in case the date is not accessible in this method
        try:
            startDate = formatDateTime(self.startDT)
        except:
            startDate = ""

        # ---- Email user ----

        to = firstName = None
        if self.createdByUser(): # Imported bookings does not have creator
            to = self.createdByUser().getEmail()
            firstName = self.createdByUser().getFirstName()
        else:
            to = self.contactEmail
            firstName = "User"

        if to:
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] REJECTED Booking on " + startDate
            wc = WTemplated( 'RoomBookingEmail_2UserAfterBookingRejection' )
            text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self, 'firstName':firstName, 'reason':reason, 'date':date } )
            fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            addrs = []
            if debug:
                addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
            else:
                addrs.append( to )
                if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                    addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
            emails.append(maildata)
        return emails

    def notifyAboutConfirmation( self ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) user about reservation acceptance.
        Called after reject().
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []

        # Fix by David: include date in this mails too. I have put a try...except in case the date is not accessible in this method
        try:
            startDate = formatDateTime(self.startDT)
        except:
            startDate = ""

        # ---- Email user ----

        to = firstName = None
        if self.createdByUser(): # Imported bookings does not have creator
            to = self.createdByUser().getEmail()
            firstName = self.createdByUser().getFirstName()
        else:
            to = self.contactEmail
            firstName = "User"

        if to:
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Confirmed Booking on " + startDate
            wc = WTemplated( 'RoomBookingEmail_2UserAfterBookingConfirmation' )
            text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self, 'firstName':firstName } )
            fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            addrs = []
            if debug:
                addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
            else:
                addrs.append( to )
                if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                    addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
            emails.append(maildata)

        # ---- Email AVC Support ----

        if self.isConfirmed  and  self.usesAVC: # Inform only about confirmed bookings
            to = Location.parse( self.locationName ).getAVCSupportEmails()
            if to:
                subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] New Booking on " + startDate
                wc = WTemplated( 'RoomBookingEmail_2AVCSupportAfterBookingInsertion' )
                text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation': self } )
                fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
                addrs = []
                if debug:
                    addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
                else:
                    addrs += to
                    if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                        addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
                maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
                emails.append(maildata)
        return emails

    def notifyAboutUpdate( self ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) user and responsible about reservation update.
        Called after update().
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []

        # Fix by David: include date in this mails too. I have put a try...except in case the date is not accessible in this method
        try:
            startDate = formatDateTime(self.startDT)
        except:
            startDate = ""

        # ---- Email user ----

        if self.createdByUser(): # Imported bookings does not have creator
            to = self.createdByUser().getEmail()
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Booking Modified on " + startDate
            wc = WTemplated( 'RoomBookingEmail_2UserAfterBookingModification' )
            text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self } )
            fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            addrs = []
            if debug:
                addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
            else:
                addrs.append( to )
                if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                    addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
            emails.append(maildata)

        # ---- Email responsible ----

        toMain = self.room.getResponsible().getEmail()

        subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Booking Modified on " + startDate
        wc = WTemplated( 'RoomBookingEmail_2ResponsibleAfterBookingModification' )
        text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self } )
        fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
        addrs = []
        if debug:
            addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
        else:
            addrs.append( toMain )
            if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            if self.room.customAtts.get( 'notification email', None ):
                addrs.append(self.room.customAtts.get( 'notification email' ).strip())
        maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
        emails.append(maildata)

        # ---- Email AVC Support ----

        if self.isConfirmed  and  self.usesAVC: # Inform only about confirmed bookings
            to = Location.parse( self.locationName ).getAVCSupportEmails()
            if to:
                subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Modified booking on " + startDate
                wc = WTemplated( 'RoomBookingEmail_2AVCSupportAfterBookingModification' )
                text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation': self } )
                fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
                addrs = []
                if debug:
                    addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
                else:
                    addrs += to
                    if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                        addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
                maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
                emails.append(maildata)

        return emails

    def requestProlongation( self ):
        """
        FINAL (not intented to be overriden)
        Heavy reservations require user confirmation every x weeks.
        This method sends user an e-mail, asking him to confirm (prolong)
        the reservation for the next x weeks.
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []

        # Fix by David: include date in this mails too. I have put a try...except in case the date is not accessible in this method
        try:
            startDate = formatDateTime(self.startDT)
        except:
            startDate = ""

        # ---- Email user ----
        if self.createdByUser(): # Imported bookings does not have creator
            to = self.createdByUser().getEmail()
            subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Request for Booking Prolongation on " + startDate
            wc = WTemplated( 'RoomBookingEmail_2UserRequestProlongation' )
            text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self } )
            fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
            addrs = []
            if debug:
                addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
            else:
                addrs.append( to )
                if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                    addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
            emails.append(maildata)
        return emails

    def notifyAboutLackOfProlongation( self ):
        """
        FINAL (not intented to be overriden)
        Notifies (e-mails) responsible that user
        did not prolong his HEAVY booking.
        """
        from MaKaC.webinterface.wcomponents import WTemplated
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        emails = []

        # ---- Email responsible ----

        toMain = self.room.getResponsible().getEmail()

        subject = NOTIFICATION_SUBJECT_PREFIX + " [" + self.room.getFullName() + "] Consider Rejecting This Booking"
        wc = WTemplated( 'RoomBookingEmail_2ResponsibleConsiderRejecting' )
        text = TEST_VERSION_WARNING + wc.getHTML( { 'reservation':self } )
        fromAddr = EMAIL_FROM_PREFIX+HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
        addrs = []
        if debug:
            addrs.append( EMAIL_FOR_DEBUG_NOTIFICATIONS )
        else:
            addrs.append( toMain )
            if EMAIL_FOR_CATCH_ALL_NOTIFICATIONS:
                addrs.append( EMAIL_FOR_CATCH_ALL_NOTIFICATIONS )
            if self.room.customAtts.get( 'notification email', None ):
                addrs.append(self.room.customAtts.get( 'notification email' ).strip())
        maildata = { "fromAddr": fromAddr, "toList": addrs, "subject": subject, "body": text }
        emails.append(maildata)
        return emails

    # Query ------------------------------------------------------------------

    @staticmethod
    def getReservations( *args, **kwargs ):
        """
        Generic, universal query. Returns reservations meeting specified conditions.

        It is 'query by example'. You specify conditions by creating
        the object and passing it to the method.

        All arguments are optional:

        resvID - reservation ID
        resvExample - example ReservationBase object
        rooms - _list_ of RoomBase objects

        Examples:

        # 1. Get all reservations for Dec 2006, booked for Jean

        resvEx = ReservationBase()
        resvEx.startDT = datetime( 2006, 12, 1, 0 )     # 2006-12-01 00:00
        resvEx.endDT = datetime( 2006, 12, 31, 23, 59 ) # 2006-12-31 23:59
        resvEx.bookedForName = "Jean"

        reservations = ReservationBase.getReservations( resvExample = resvEx )

        # 2. Get all reservations of the room "AT AMPHITHEATRE" in Dec 2006

        # copy above, then:
        room = RoomBase.getRooms( roomName = 'AT AMPHITHEATRE' )
        reservations = ReservationBase.getReservations( resvExample = resvEx, rooms = [room] )
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        return Factory.newReservation().getReservations( **kwargs )

    # Time-play: repeatings, overlapings, etc.

    def getCollisions( self, sansID = None, rooms = None, boolResult = False ):
        """
        Returns all collisions with other reservations for the same room,
        or empty list [] if none collisions were found.

        Collisions are returned as list of Collision objects.

        Reservation having id == sansID is omited (use it to
        skip conflicts with self).
        """
        # IMPLEMENTATION:
        #
        # Reservation is possible if for the given room x,
        # there are no overlaping reservations.

        # Reservation may be seen as a group of 1-day periods.
        # For non-repeating reservation, it is exactly one period.
        # For repeating ones, every repeating creates small period (i.e. 4 hours).

        # Two reservations does not overlap <=> there are no overlaping periods.

        # Therefore every period of r1 must be checked against every period of r2

        # 1) Get all reservations that may have impact on the candidate.
        # 2) Split candidate and other reservations into 1-day periods.
        # 3) Check every candidate period against every other period.
        # 4) Remember and return collisions.

        if ( rooms == None and self.room == None ) or self.startDT == None or self.endDT == None:
            raise 'room, startDT, endDT fields must not be None'

        if rooms == None:
            rooms = [ self.room ]

        resvEx = ReservationBase()
        resvEx.startDT = self.startDT
        resvEx.endDT = self.endDT
        resvEx.repeatability = self.repeatability
        resvEx.isRejected = False
        resvEx.isCancelled = False
        # In general attributes from self cannot be copied to
        # searching example. Self is i.e. new booking someone tries
        # to insert, so it has all attributes.
        # However, it is safe for isConfirmed == None, because
        # isConfirmed is None only when explitly set.
        # Normally isConfirmed defaults to True.
        if self.isConfirmed == None: # None here is very important; 'False' differs
            resvEx.isConfirmed = None # Force to include not confirmed bookings

        candidatePeriods = self.splitToPeriods()
        days = ( period.startDT.date() for period in candidatePeriods )

        from MaKaC.plugins.RoomBooking.CERN.reservationCERN import ReservationCERN
        resvs = ReservationCERN.getReservations( location = self.locationName,
                                                      resvExample = resvEx,
                                                      rooms = rooms,
                                                      #archival = False,
                                                      days = days )

        resvs = filter( lambda r: r.id != sansID, resvs )

        collisions = []
        if len( resvs ) == 0:
            return [] # No collisions

        potentialColliders = []
        for resv in resvs:
            potentialColliders.append( ( resv, resv.splitToPeriods(endDT=self.endDT) ) )

        for r in potentialColliders:
            resv = r[0]
            colliderPeriods = r[1]
            for candidatePeriod in candidatePeriods:
                for colliderPeriod in colliderPeriods:
                    if doesPeriodsOverlap( candidatePeriod, colliderPeriod ):
                        if boolResult:
                            # There is at least one collision
                            return True
                        else:
                            # Collect collisions
                            collisions.append( Collision( overlap( candidatePeriod, colliderPeriod ), resv ) )

        return collisions

    def getNextRepeating( self, afterDT = None ):
        """
        Returns Period of the next repeating (occurence).
        For non-repeating reservations simply returns
        the time of the reservation (also as Period object).
        Returns None if reservation will never repeat after afterDT.
        """
        if not afterDT:
            afterDT = datetime.now()
        # Do not look in the specified date
        afterDT = datetime( afterDT.year, afterDT.month, afterDT.day, 23, 59, 59 )

        # No repeatings after afterDT
        if afterDT > self.endDT:
            return None

        # Non-repeating reservation
        if self.repeatability == None:
            if afterDT < self.startDT:
                return Period( self.startDT, self.endDT )
            else:
                return None

        # Before first repeating
        if afterDT < self.startDT:
            retEndDT = datetime( self.startDT.year, self.startDT.month, self.startDT.day, self.endDT.hour, self.endDT.minute )

            if self.dayIsExcluded( self.startDT.date() ):
                return self.getNextRepeating( self.startDT )  # Recurrently ask for next
            return Period( self.startDT, retEndDT )

        # Constant period repeatings
        if self.repeatability in ( RepeatabilityEnum.daily, RepeatabilityEnum.onceAWeek,
                                   RepeatabilityEnum.onceEvery2Weeks,
                                   RepeatabilityEnum.onceEvery3Weeks ):
            # Number of days between repeatings
            diff = RepeatabilityEnum.rep2diff[ self.repeatability ]
            # Candidate for next repeating: next day
            repCandidateDT = afterDT + timedelta( 1 )
            # How much to early is the candidate? (days)
            toEarly = (diff - (( repCandidateDT - self.startDT ).days % diff )) % diff
            # Add differene
            repCandidateDT = repCandidateDT + timedelta( toEarly )
            # Now it should represent next repeating
            retStartDT = datetime( repCandidateDT.year, repCandidateDT.month, repCandidateDT.day, self.startDT.hour, self.startDT.minute )
            retEndDT = datetime( repCandidateDT.year, repCandidateDT.month, repCandidateDT.day, self.endDT.hour, self.endDT.minute )

            if self.dayIsExcluded( retStartDT.date() ):
                return self.getNextRepeating( retStartDT )  # Recurrently ask for next
            return Period( retStartDT, retEndDT )

        # Monthly repeatings
        if self.repeatability == RepeatabilityEnum.onceAMonth:
            # Candidate for next repeating: next day
            repCandidateDT = afterDT + timedelta( 1 )

            weekDayDiff = self.weekDay - repCandidateDT.weekday()
            if weekDayDiff < 0:
                weekDayDiff += 7
            repCandidateDT += timedelta( weekDayDiff ) # Try next day...

            while weekNumber( repCandidateDT ) != self.weekNumber:
                repCandidateDT += timedelta( 7 )  # Try next week...

            retStartDT = datetime( repCandidateDT.year, repCandidateDT.month, repCandidateDT.day, self.startDT.hour, self.startDT.minute )
            retEndDT = datetime( repCandidateDT.year, repCandidateDT.month, repCandidateDT.day, self.endDT.hour, self.endDT.minute )

            if self.dayIsExcluded( retStartDT.date() ):
                return self.getNextRepeating( retStartDT )  # Recurrently ask for next
            return Period( retStartDT, retEndDT )

        raise 'Unknown repeatability type.'

    def overlapsOn( self, startDT, endDT ):
        """
        Does the reservation overlap on the period (startDT, endDT)?

        This method takes repeatings into consideration.

        Please note that for repeating reservations,
        startDate and endDate DOES NOT imply the overlaping.

        It is necessary to compute whether specific repeating
        will fall into the requested period. This computation
        must include not only subsequent repeatings of the
        reservation, but also exceptions to those repeatings.

        (Reservation may repeat every week through the whole
        year, except date1, date2 and date3...).
        """

        theyOverlap = doesPeriodsOverlap( self.startDT, self.endDT, startDT, endDT )
        if not theyOverlap:
            return False

        # NO REPEATINGS
        if self.repeatability == None:
            return True    # We do not have to check further

        overlapStartDT, overlapEndDT = overlap( self.startDT, self.endDT, startDT, endDT )

        # DAILY REPEATINGS
        if self.repeatability == RepeatabilityEnum.daily:
            for day in iterdays( overlapStartDT, overlapEndDT ):
                if not self.dayIsExcluded( day.date() ):
                    return True
            return False

        weekdaysInPeriod = []
        for day in iterdays( overlapStartDT, overlapEndDT ):
            if day.weekday() == self.weekDay:
                if not self.dayIsExcluded( day.date() ):
                    weekdaysInPeriod.append( day )
        if len( weekdaysInPeriod ) == 0:
            return False

        # ONCE A WEEK
        if self.repeatability == RepeatabilityEnum.onceAWeek:
            return True

        # ONCE EVERY 2 OR 3 WEEKS
        if self.repeatability in ( RepeatabilityEnum.onceEvery2Weeks, RepeatabilityEnum.onceEvery3Weeks ):
            # Check if candidate weekday is in the overlaping period
            for weekday in weekdaysInPeriod:
                if self.repeatability == RepeatabilityEnum.onceEvery2Weeks:
                    # Check if the weekday is in the SECOND week (not the following week)
                    # => There must be exactly 14 days between previous repeating
                    # and the present one. So, the difference between initial repeating
                    # (startDT) and any next repeating must divide by 14.
                    if (weekday - self.startDT).days % 14 == 0:
                        return True
                if self.repeatability == RepeatabilityEnum.onceEvery3Weeks:
                    # By analogy to the above, difference must divide by 21.
                    if (weekday - self.startDT).days % 21 == 0:
                        return True
            return False

        # ONCE A MONTH
        if self.repeatability == RepeatabilityEnum.onceAMonth:
            requiredWeekNumber = self.weekNumber
            # Does the period contain weekNumber?
            for weekday in weekdaysInPeriod:
                if weekNumber( weekday ) == requiredWeekNumber:
                    return True
            return False

        raise "Unknown repeatability type"

    # Excluded days management ----------------------------------------------

    # Repeating reservations repeat in certain period with
    # specific frequency. However, there may be *exceptions*
    # to this general pattern. It is possible to *exclude*
    # some days. It allows to create resvs like:
    # "Repeat every week through the whole year, except
    #  date1, date2 and date3".
    #
    # The following methods allow to manage 'excluded days' list
    # for a reservation.

    def getExcludedDays( self ):
        """
        Returns list of excluded dates in random order.
        Example:  [ date1, date2, date3, ... ]
        Dates are of date type (NOT datetime).
        """
        if self.repeatability == None:
            return 'Not applicable to non-repeating reservations.'

    def setExcludedDays( self, excludedDays ):
        """
        Sets list of excluded dates. Accepts:
        [ date1, date2, date3, ... ]
        Dates are of date type (NOT datetime).
        """
        if self.repeatability == None:
            return 'Not applicable to non-repeating reservations.'
        for d in excludedDays:
            if not isinstance( d, date ):
                raise 'excludedDays must contain only objects of date type (NOT datetime)'

    def excludeDay( self, dayD ):
        """
        Inserts dayD into list of excluded days.
        dayD should be of date type (NOT datetime).
        """
        if self.repeatability == None:
            return 'Not applicable to non-repeating reservations.'
        if not isinstance( dayD, date ):
            raise 'dayD must be of date type (NOT datetime)'

    def includeDay( self, dayD ):
        """
        Inserts dayD into list of excluded days.
        dayD should be of date type (not datetime).
        """
        if self.repeatability == None:
            return 'Not applicable to non-repeating reservations.'
        if not isinstance( dayD, date ):
            raise 'dayD must be of date type (NOT datetime)'

    def dayIsExcluded( self, dayD ):
        """
        Returns true if dayD is among the excluded days. False otherwise.
        """
        if self.repeatability == None:
            return 'Not applicable to non-repeating reservations.'
        if not isinstance( dayD, date ):
            raise 'dayD must be of date type (NOT datetime)'


    # Statistical ------------------------------------------------------------

    @staticmethod
    def countReservations():
        """
        Counts reservations meeting specified conditions.
        Usage: like getReservations(). Tip: for common statistics,
        there are ready methods, i.e. getNumberOfLiveReservations().
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        return Factory.newReservation().countReservations()

    @staticmethod
    def getNumberOfReservations():
        """
        Returns total number of reservations in database.
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        return Factory.newReservation().getNumberOfReservations()

    @staticmethod
    def getNumberOfLiveReservations():
        """
        Returns number of live reservations in database.
        Reservation is live if it has impact in the future.
        Therefore it is:
        - not archival
        - neither cancelled nor rejected
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        return Factory.newReservation().getNumberOfLiveReservations()

    @staticmethod
    def getNumberOfArchivalReservations():
        """
        Returns number of archival reservations in database.
        Reservation is archival if it has end date in the past.
        Cancelled future reservations are not consider as archival.
        """
        # Simply redirect to the plugin
        from MaKaC.rb_factory import Factory
        return Factory.newReservation().getNumberOfArchivalReservations()

    @staticmethod
    def getReservationStats( **kwargs ):
        """
        Used to generate statistics like this:

                    Valid      Cancelled      Rejected
        Live            x              x             x
        Archival        x              x             x

        Returns dictionary with the following keys:
        liveValid, liveCancelled, liveRejected
        archivalValid, archivalCancelled, archivalRejected
        """
        location = kwargs.get( 'location', Location.getDefaultLocation().friendlyName )
        allResvs = ReservationBase.getReservations( location = location )     # Run Forest, run! :)
        stats = { \
                     'liveValid': 0,
                     'liveCancelled': 0,
                     'liveRejected': 0,
                     'archivalValid': 0,
                     'archivalCancelled': 0,
                     'archivalRejected': 0,
                 }
        for r in allResvs:
            if r.isArchival:
                if r.isCancelled:
                    stats['archivalCancelled'] += 1
                elif r.isRejected:
                    stats['archivalRejected'] += 1
                else: # r.isValid (must be)
                    stats['archivalValid'] += 1
            else: # live
                if r.isCancelled:
                    stats['liveCancelled'] += 1
                elif r.isRejected:
                    stats['liveRejected'] += 1
                else: # r.isValid (must be)
                    stats['liveValid'] += 1

        return stats

    @staticmethod
    def getRoomReservationStats(room):
        """
        Used to generate statistics like this:

                    Valid      Cancelled      Rejected
        Live            x              x             x
        Archival        x              x             x

        Returns dictionary with the following keys:
        liveValid, liveCancelled, liveRejected
        archivalValid, archivalCancelled, archivalRejected
        """
        location = Location.getDefaultLocation().friendlyName
        allResvs = ReservationBase.getReservations( rooms = [ room ] )     # Run Forest, run! :)
        stats = { \
                     'liveValid': 0,
                     'liveCancelled': 0,
                     'liveRejected': 0,
                     'archivalValid': 0,
                     'archivalCancelled': 0,
                     'archivalRejected': 0,
                 }
        for r in allResvs:
            if r.isArchival:
                if r.isCancelled:
                    stats['archivalCancelled'] += 1
                elif r.isRejected:
                    stats['archivalRejected'] += 1
                else: # r.isValid (must be)
                    stats['archivalValid'] += 1
            else: # live
                if r.isCancelled:
                    stats['liveCancelled'] += 1
                elif r.isRejected:
                    stats['liveRejected'] += 1
                else: # r.isValid (must be)
                    stats['liveValid'] += 1
        return stats

    @staticmethod
    def findSoonest( resvs, afterDT = datetime.now() ):
        if not resvs: return None

        nextRepeating = datetime( 2050, 01, 01 )
        ret = resvs[0]
        for r in resvs:
            nrep = r.getNextRepeating( afterDT = afterDT )
            if nrep and nrep.startDT < nextRepeating:
                nextRepeating = nrep.startDT
                ret = r
        return ret


    # "System" ---------------------------------------------------------------

    def checkIntegrity( self ):
        """
        FINAL (not intented to be overriden)
        Checks whether:
        - all required attributes has values
        - values are of correct type
        - semantic coherence (i.e. star date <= end date)
        """
        from MaKaC.rb_room import RoomBase
        # list of errors
        errors = []

        # locationName - derived
        # guid - derived
        # weekDay - derived
        # weekNumber - derived

        # check presence and types of arguments
        # =====================================================
        if self.id != None:         # Only for existing objects
            checkPresence( self, errors, 'id', int )
        checkPresence( self, errors, 'room', RoomBase )
        checkPresence( self,errors, '_utcStartDT', datetime )
        checkPresence( self,errors, '_utcEndDT', datetime )
        checkPresence( self,errors, '_utcCreatedDT', datetime )
        if self.repeatability != None:
            checkPresence( self, errors, 'repeatability', int )
        checkPresence( self, errors, 'bookedForName', str )
        #checkPresence( self, errors, 'contactEmail', str )
        #checkPresence( self, errors, 'contactPhone', str )
        #checkPresence( self, errors, 'createdBy', int )
        checkPresence( self, errors, 'reason', str )
        checkPresence( self, errors, 'reason', str )

        checkPresence( self, errors, 'isRejected', bool )
        checkPresence( self, errors, 'isCancelled', bool )

        # check semantic integrity
        # =====================================================
        # start < end
        if self.startDT > self.endDT:
            errors.append( 'startDT must be before endDT' )
        if self.startDT.time() > self.endDT.time():
            errors.append( 'startT must be before endT' )
        # room exists
        roomID = self.room.id
        roomLocation = self.room.locationName
        rooms = CrossLocationQueries.getRooms( location = roomLocation, roomID = roomID )
        if not rooms:
            errors.append ( 'room ' + self.room.guid + ' not found in db' )
        # collisions (only for valid ones)
        if self.isValid:
            if self.id:
                col = self.getCollisions( sansID = self.id )
            else:
                col = self.getCollisions()
            if len( col ) > 0:
                #errors.append ( 'the reservation collides with existing ones' )
                print "Candidate: --------------------------------"
                print self
                print "Collision 1: ------------------------------"
                print col[0].withReservation

        if errors:
            raise str( errors )

    # Indico architecture  AND  authorization -----------------------

    __owner = None

    def getLocator( self ):
        """
        FINAL (not intented to be overriden)
        Returns a globaly unique identification
        encapsulated in a Locator object
        """
        owner = self.getOwner()
        if owner:
            loc = owner.getLocator()
        else:
            from MaKaC.common.Locators import Locator
            loc = Locator()
        # There is no something like "resvLocation" since
        # location of a reservation always equals location
        # of a room it concerns.
        loc["roomLocation"] = self.locationName
        loc["resvID"] = self.id
        return loc

    def setOwner( self, owner ):
        """
        FINAL (not intented to be overriden)
        Owner in terms of "parent", i.e. conference
        """
        oryg = self._p_changed
        self.__owner = None
        if owner:
            self.__owner = owner.getId()#Impersistant( owner )
        self._p_changed = oryg

    def getOwner( self ):
        """
        FINAL (not intented to be overriden)
        Owner in terms of "parent", i.e. conference
        """
        ####---FIXING THE USE OF IMPERSISTANT CLASS-----
        if isinstance(self.__owner, Impersistant):
            o = self.__owner.getObject()
            if o:
                self.__owner=o.getId()
            else:
                self.__owner=None
        ####---ENDO OF FIXING THE USE OF IMPERSISTANT CLASS-----
        if self.__owner:
            return ConferenceHolder().getById(self.__owner) #self.__owner.getObject() # Wrapped in Impersistant

        return None

    def isProtected( self ):
        """
        FINAL (not intented to be overriden)
        The one must be logged in to do anything in RB module.
        """
        return True

    def canView( self, accessWrapper ):
        """
        FINAL (not intented to be overriden)
        Reservation details are public - anyone who is
        authenticated can view.
        """
        return True

    def canModify( self, accessWrapper ):
        """
        FINAL (not intented to be overriden)
        The following persons are authorized to modify a booking:
        - owner (the one who created the booking)
        - responsible for a room
        - admin (of course)
        """
        if accessWrapper == None:
            return False

        user = None
        if isinstance( accessWrapper, AccessWrapper ):
            user = accessWrapper.getUser()
        elif isinstance( accessWrapper, Avatar ):
            user = accessWrapper
        else:
            raise 'canModify requires either AccessWrapper or Avatar object'
        if not user:
            return False
        can = user.isAdmin() or \
            self.isOwnedBy( user ) or \
            self.room.isOwnedBy( user )
        return can

    def canCancel( self, user ):
        """ Owner can cancel """
        if user == None:
            return False
        return self.isOwnedBy( user ) or user.isAdmin()

    def canReject( self, user ):
        """ Responsible can reject """
        if user == None:
            return False
        return self.room.isOwnedBy( user ) or user.isAdmin()

    def canDelete( self, user ):
        """ Only admin can delete """
        if user == None:
            return False
        return user.isAdmin()

    def isOwnedBy( self, avatar ):
        """
        Returns True if avatar is the one who inserted this
        reservation. False otherwise.
        """
        if not self.createdBy:
            return None
        if self.createdBy == avatar.id:
            return True
        return False

    # Required by Indico architecture
    def getAccessKey( self ): return ""

    def createdByUser( self ):
        if self.createdBy == None:
            return None
        user = AvatarHolder().getById( self.createdBy )
        if user == None:
            return None
        return user


    def splitToPeriods( self, endDT = None, startDT = None ):
        """
        Returns the list of Periods that represent this reservation.

        For non-repeating reservations it is just the reservation period.
        For repeating ones, the list will include all repeatings.
        """
        if startDT is None:
            lastDT = self.startDT - timedelta( 1 )   # One day before the beginning
        else:
            lastDT = startDT - timedelta( 1 )

        periods = []

        while True:
            period = self.getNextRepeating( lastDT )
            if period is None or (endDT != None and period.startDT > endDT):
                return periods
            lastDT = period.startDT
            periods.append( period )

    # ==== Private ===================================================

    # datetime (DT) converters --------

    def _getStartDT( self ):
        return fromUTC( self._utcStartDT )

    def _setStartDT( self, localNaiveDT ):
        self._utcStartDT = toUTC( localNaiveDT )

    def _getEndDT( self ):
        return fromUTC( self._utcEndDT )

    def _setEndDT( self, localNaiveDT ):
        self._utcEndDT = toUTC( localNaiveDT )

    def _getCreatedDT( self ):
        return fromUTC( self._utcCreatedDT )

    def _setCreatedDT( self, localNaiveDT ):
        self._utcCreatedDT = toUTC( localNaiveDT )

    # --------------------------------

    def _getIsValid( self ):
        """
        FINAL (not intented to be overriden)
        """
        if self.isRejected == None or self.isCancelled == None or self.isConfirmed == None:
            return None
        if self.isConfirmed and not self.isRejected and not self.isCancelled:
            return True
        return False

    def _isArchival( self ):
        """
        FINAL (not intented to be overriden)
        """
        if self.endDT == None:
            return None
        return self.endDT < datetime.now()

    def _isHeavy( self ):
        """
        Defines when reservation is considered "heavy".
        """
        if self.endDT == None or self.startDT == None or self.room == None:
            return None

        # Conditions of heavines - the booking:
        # 1. Is for room which is publically reservable AND
        # 2. Is repeating AND
        # 3. Lasts longer than one month AND
        # 4. Takes more than x hours monthly

        if not self.room.isReservable:
            return False
        if self.repeatability == None:
            return False
        if ( self.endDT - self.startDT ).days < 30:
            return False

        HOURS_MONTHLY_TO_CONSIDER_HEAVY = 15
        periods = self.splitToPeriods()
        totalHours = 0.0
        for p in periods:
            totalHours += ( p.endDT - p.startDT ).seconds / 3600.0
        hoursPerMonth = totalHours / ( self.endDT - self.startDT ).days * 30
        if hoursPerMonth < HOURS_MONTHLY_TO_CONSIDER_HEAVY:
            return False

        return True

    def _getWeekDay( self ):
        """
        FINAL (not intented to be overriden)
        """
        if self.startDT != None and self.repeatability in (
            RepeatabilityEnum.onceAWeek, RepeatabilityEnum.onceEvery2Weeks,
            RepeatabilityEnum.onceEvery3Weeks, RepeatabilityEnum.onceAMonth ):
            return self.startDT.weekday()
        return None

    def _getWeekNumber( self ):
        if self.repeatability == RepeatabilityEnum.onceAMonth and self.startDT != None:
            return weekNumber( self.startDT )
        return None

    def _getLocationName( self ):
        if self.__class__.__name__ == 'ReservationBase':
            return None #Location.getDefaultLocation().friendlyName
        return self._getLocationName() # Subclass

    def _getGuid( self ):
        if self.locationName == None:
            return None
        return ReservationGUID( Location.parse( self.locationName ), self.id )

    def _eval_str( self, s ):
        ixPrv = 0
        ret = ""

        while True:
            ix = s.find( "#{", ixPrv )
            if ix == -1:
                break
            ret += s[ixPrv:ix] # verbatim
            ixPrv = s.index( "}", ix + 2 ) + 1
            try:
                ret += str( eval( s[ix+2:ixPrv-1] ) )
            except: pass

        return ret

    def __str__( self ):
        return self._eval_str(
"""
         location: #{self.locationName}
               id: #{self.id}

             room: #{self.room.name}
           starDT: #{self.startDT}
            endDT: #{self.endDT}
        createdDT: #{self.createdDT}

    repeatability: #{self.repeatability}
          weekDay: #{self.weekDay}
       weekNumber: #{self.weekNumber}

    bookedForName: #{self.bookedForName}
     contactEmail: #{self.contactEmail}
     contactPhone: #{self.contactPhone}
        createdBy: #{self.createdBy}
           reason: #{self.reason}

       isRejected: #{self.isRejected}
      isCancelled: #{self.isCancelled}

      isConfirmed: #{self.isConfirmed}
          isValid: #{self.isValid}
       isArchival: #{self.isArchival}
          isHeavy: #{self.isHeavy}
"""
        )

    def _getVerboseRepetition( self ):
        s = RepeatabilityEnum.rep2description[ self.repeatability ]
        if self.weekDay != None:
            s += " on %s" % WeekDayEnum.week2desc[self.weekDay]

        return s

    def _getVerboseStatus( self ):
        s = ""
        if self.isValid:
            s += "Valid"
        else:
            if self.isCancelled:
                s += " Cancelled"
            if self.isRejected:
                s += " Rejected"
            if not self.isConfirmed:
                s += " Not&nbsp;confirmed"
        if self.isArchival:
            s += " Archival"
        else:
            s += " Live"
        if self.isHeavy:
            s += " Heavy"
        s = ', '.join( s.strip().split( ' ' ) )

        return s

    def _getVerboseCreatedBy( self ):
        user = self.createdByUser()
        if user == None:
            return ""
        return user.getFullName()


    def __cmp__( self, other ):
        if self.__class__.__name__ == 'NoneType' and other.__class__.__name__ == 'NoneType':
            return 0
        if self.__class__.__name__ == 'NoneType':
            return cmp( None, 1 )
        if other.__class__.__name__ == 'NoneType':
            return cmp( 1, None )

        if self.id != None  and  other.id != None:
            if self.id == other.id:
                return 0
            else:
                return cmp(self.id, other.id)

        c = cmp( self.room, other.room )
        if c == 0 and self.startDT and self.endDT and other.startDT and other.endDT:
            yesterday = datetime.now() - timedelta( 1 )
            nrSelf = self.getNextRepeating( afterDT = yesterday )
            nrOther = other.getNextRepeating( afterDT = yesterday )
            if nrSelf or nrOther:
                if nrSelf == None:
                    return cmp( 1, None )
                if nrOther == None:
                    return cmp( None, 1 )
                c = cmp( nrSelf.startDT, nrOther.startDT )
        return c

    # ==== Properties ===================================================

    # DO NOT set default values here, since query-by-example will change!!!

    # Attributes that take part in similarity comparison

    id = None             # int - artificial ID; initialy value from oracle db
    locationName = property( _getLocationName ) # location (plugin) name
    guid = property( _getGuid ) # ReservationGUID

    # Basic

    room = None           # RoomBase - room that is reserved

    # DO NOT use these directly!
    # Use properties instead
    _utcStartDT = None
    _utcEndDT = None
    _utcCreatedDT = None

    startDT = property( _getStartDT, _setStartDT )    # datetime - when the reservation starts; internally UTC, accepted and returned in local/DST
    endDT = property( _getEndDT, _setEndDT )      # datetime - when the reservation ends; internally UTC, accepted and returned in local/DST
    createdDT = property( _getCreatedDT, _setCreatedDT )  # datetime - when the booking was created; internally UTC, accepted and returned in local/DST

    # Repeatability

    repeatability = None  # int - one of the RepeatabilityEnum
    weekDay = property( _getWeekDay )   # int - one of the WeekDayEnum
    # weekNumber - int, 1-5, in which week of the month the repeating takes place.
    # Applicable only for repeatability == OnceAMonth:
    weekNumber = property( _getWeekNumber )

    # Who and why
    bookedForName = None  # str - for whom it is booked; free text
    contactEmail = None   # str - contact; typically the person for whom the booking is done
    contactPhone = None   # str - contact; typically the person for whom the booking is done
    createdBy = None      # str/avatar_id - who has created the booking
    reason = None         # str - justification for booking
    rejectionReason = None# str - justification for rejection

    # Status
    isConfirmed = True    # bool - whether the booking is confirmed  (defaults to True to keep semantic of existing code)
    isRejected = None     # bool - whether was rejected by responsible
    isCancelled = None    # bool - whether was cancelled by user

    # Reservation is valid when neither rejected nor cancelled
    isValid = property( _getIsValid )

    # Reservation is archival if endDT is in the past
    isArchival = property( _isArchival )

    # Whether it uses Audio Visual Conferencing equipment
    usesAVC = None
    needsAVCSupport = None

    # True if reservation requires repeating confirmations
    isHeavy = property( _isHeavy )

    # ==== Verbose Properties ================================================

    # These are read-only, "redundant" properties designated for end user (GUI)
    # Therefore their purpose is to return human-readable text

    verboseRepetition = property( _getVerboseRepetition )
    verboseStatus = property( _getVerboseStatus )
    verboseCreatedBy = property( _getVerboseCreatedBy )

class Collision( object ):
    """
    Simple helper class for storing information about collision:
    - with whom (which reservation) the collision was noticed
    - overlaping period (max 1 day!)
    """
    withReservation = None # With which reservation
    startDT         = None # Overlaping period - begin
    endDT           = None # Overlaping period - end

    def __init__( self, periodTuple, resv ):
        self.startDT, self.endDT = periodTuple
        self.withReservation = resv

# ============================================================================
# ================================== TEST ====================================
# ============================================================================

class Test:

    @staticmethod
    def weekNumber():
        resv = ReservationBase()
        resv.startDT = datetime( 2006, 9, 22 ) # Fourth Friday
        assert( resv.weekNumber == None )      # No repeating
        resv.repeatability = RepeatabilityEnum.onceAMonth
        assert( resv.weekNumber == 4 )
        resv.startDT = datetime( 2006, 9, 30 )
        assert( resv.weekNumber == 5 )
        resv.startDT = datetime( 2006, 9, 1 )
        assert( resv.weekNumber == 1 )

    @staticmethod
    def overlapsOn():
        resv = ReservationBase()

        resv.startDT = datetime( 2006, 1, 1, 10 )
        resv.endDT = datetime( 2006, 8, 31, 12 )

        # Dates does not overlap
        assert( not resv.overlapsOn( datetime( 2006, 9, 1 ) , datetime( 2006, 9, 30 ) ) )
        # Hours does not overlap
        assert( not resv.overlapsOn( datetime( 2006, 8, 31, 12, 1 ) , datetime( 2006, 9, 30, 13 ) ) )
        # Overlap
        assert( resv.overlapsOn( datetime( 2006, 8, 31, 9 ) , datetime( 2006, 9, 30, 11 ) ) )

        # ONCE A WEEK
        resv.repeatability = RepeatabilityEnum.onceAWeek

        # Weekdays does not overlap (Sunday vs Monday:Saturday)
        assert( not resv.overlapsOn( datetime( 2006, 8, 7, 10 ), datetime( 2006, 8, 12, 12 ) ) )
        # Overlap
        assert( resv.overlapsOn( datetime( 2006, 8, 7, 10 ), datetime( 2006, 8, 13, 12 ) ) )

        # ONCE EVERY 2 WEEKS
        resv.repeatability = RepeatabilityEnum.onceEvery2Weeks

        # The following week
        assert( not resv.overlapsOn( datetime( 2006, 1, 8, 10 ), datetime( 2006, 1, 14, 12 ) ) )
        # Overlap
        assert( resv.overlapsOn( datetime( 2006, 1, 15, 10 ), datetime( 2006, 1, 15, 12 ) ) )

        # ONCE EVERY 3 WEEKS
        resv.repeatability = RepeatabilityEnum.onceEvery3Weeks

        # The following week
        assert( not resv.overlapsOn( datetime( 2006, 1, 8, 10 ), datetime( 2006, 1, 14, 12 ) ) )
        # The second week
        assert( not resv.overlapsOn( datetime( 2006, 1, 15, 10 ), datetime( 2006, 1, 15, 12 ) ) )
        # The 6'th week (OK)
        assert( resv.overlapsOn( datetime( 2006, 2, 10, 10 ), datetime( 2006, 2, 12, 12 ) ) )

        # ONCE A MONTH
        resv.repeatability = RepeatabilityEnum.onceAMonth

        # The following week
        assert( not resv.overlapsOn( datetime( 2006, 1, 8, 10 ), datetime( 2006, 1, 14, 12 ) ) )
        # The second week
        assert( not resv.overlapsOn( datetime( 2006, 1, 15, 10 ), datetime( 2006, 1, 15, 12 ) ) )
        # Next month, bad day
        assert( not resv.overlapsOn( datetime( 2006, 2, 6, 10 ), datetime( 2006, 2, 28, 12 ) ) )
        # 4 months later, OK
        assert( resv.overlapsOn( datetime( 2006, 5, 6, 10 ), datetime( 2006, 5, 8, 12 ) ) )

        resv.startDT = datetime( 2006, 1, 29 )
        assert( not resv.overlapsOn( datetime( 2006, 2, 1, 10 ), datetime( 2006, 3, 31, 12 ) ) )
        assert( resv.overlapsOn( datetime( 2006, 4, 20, 10 ), datetime( 2006, 4, 30, 12 ) ) )

    @staticmethod
    def statistics():
        from MaKaC.rb_factory import Factory
        Factory.getDALManager().connect()

        print "All reservations: %d" % ReservationBase.getNumberOfReservations()
        print "Archival: %d" % ReservationBase.getNumberOfArchivalReservations()
        print "Live: %d" % ReservationBase.getNumberOfLiveReservations()

        Factory.getDALManager().disconnect()

    @staticmethod
    def getNextRepeating():
        from MaKaC.rb_factory import Factory
        Factory.getDALManager().connect()

        # Every x days (daily or every 1-3 weeks)
        resv = ReservationBase.getReservations( resvID = 393966 )

        period = resv.getNextRepeating( datetime( 2005, 2, 6 ) )
        okPeriod = Period( datetime( 2007, 1, 9, 8, 30 ), datetime( 2007, 1, 9, 20 ) )
        assert( period == okPeriod )

        period = resv.getNextRepeating( datetime( 2007, 1, 9 ) )
        okPeriod = Period( datetime( 2007, 1, 16, 8, 30 ), datetime( 2007, 1, 16, 20 ) )
        assert( period == okPeriod )

        period = resv.getNextRepeating( datetime( 2007, 1, 22 ) )
        okPeriod = Period( datetime( 2007, 1, 23, 8, 30 ), datetime( 2007, 1, 23, 20 ) )
        assert( period == okPeriod )

        # Every month
        resv = ReservationBase.getReservations( resvID = 371163 )

        period = resv.getNextRepeating( datetime( 2006, 2, 12 ) )
        okPeriod = Period( datetime( 2006, 2, 13, 10 ), datetime( 2006, 2, 13, 12 ) )
        assert( period == okPeriod )

        period = resv.getNextRepeating( datetime( 2006, 2, 13 ) )
        okPeriod = Period( datetime( 2006, 3, 13, 10 ), datetime( 2006, 3, 13, 12 ) )
        assert( period == okPeriod )

        period = resv.getNextRepeating( datetime( 2006, 4, 9 ) )
        okPeriod = Period( datetime( 2006, 4, 10, 10 ), datetime( 2006, 4, 10, 12 ) )
        assert( period == okPeriod )

        Factory.getDALManager().disconnect()

    @staticmethod
    def splitToPeriods():
        from MaKaC.rb_factory import Factory
        Factory.getDALManager().connect()

        # Every x days (daily or every 1-3 weeks)
        resv = ReservationBase.getReservations( resvID = 393966 )
        periods = resv.splitToPeriods()
        assert( len( periods )  == 50 )

        # Every month
        resv = ReservationBase.getReservations( resvID = 371163 )
        periods = resv.splitToPeriods()
        assert( len( periods ) == 11 )

        Factory.getDALManager().disconnect()

    @staticmethod
    def getCollisions():
        from MaKaC.rb_factory import Factory
        from MaKaC.rb_room import RoomBase
        Factory.getDALManager().connect()

        # Every x days (daily or every 1-3 weeks)
        #resv = ReservationBase.getReservations( resvID = 393966 )
        #resv = Factory.newReservation()
        #resv = ReservationBase()
        #resv.startDT = datetime( 2006, 10, 2, 10 )
        #resv.endDT = datetime( 2006, 10, 4, 15 )
        #resv.room = RoomBase.getRooms( roomID = 4 )
        #resv.repeatability = RepeatabilityEnum.daily

        resv = Factory.newReservation()
        resv.startDT = datetime( 2006, 12, 1, 8, 30 )
        resv.endDT = datetime( 2006, 12, 2, 9, 30 )
        resv.room = RoomBase.getRooms( roomID = 89 )
        resv.repeatability = RepeatabilityEnum.daily

        collisions = resv.getCollisions()
        print "\n\nFound %d collisions.\n" % len( collisions )
        for col in collisions:
            print "Collision: ======================================================== "
            print "Period: ", col[0]
            print "With reservation: ", col[1].id

        Factory.getDALManager().disconnect()

    @staticmethod
    def tmp():
        # Available rooms
        from MaKaC.rb_factory import Factory
        from MaKaC.rb_room import RoomBase
        from MaKaC.common.db import DBMgr
        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()

        candResv = ReservationBase()
        candResv.startDT = datetime( 2007, 03, 2, 00, 01 )
        candResv.endDT = datetime( 2007, 06, 2, 23, 55 )
        candResv.room = RoomBase.getRooms( roomName = '40-4-C01' )
        candResv.repeatability = RepeatabilityEnum.onceAWeek

        print "!"
        t0 = datetime.now()
        for i in xrange( 0, 140 ):
            candResv.getCollisions( boolResult = True )
        t1 = datetime.now()
        print "! " + str( t1 - t0 )

        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def addUsesAVC():
        # Available rooms
        from MaKaC.rb_factory import Factory
        from MaKaC.common.db import DBMgr
        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()

        for resv in CrossLocationQueries.getReservations():
            resv.usesAVC = False

        Factory.getDALManager().commit()
        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def addNeedsAVCSupport():
        # Available rooms
        from MaKaC.rb_factory import Factory
        from MaKaC.common.db import DBMgr
        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()

        for resv in CrossLocationQueries.getReservations():
            resv.needsAVCSupport = False

        Factory.getDALManager().commit()
        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def addLocationAVCSupportEmails():
        # Available rooms
        from MaKaC.rb_factory import Factory
        from MaKaC.common.db import DBMgr
        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()

        for location in Location.allLocations:
            location._avcSupportEmails = []

        Location.parse( "CERN" ).setAVCSupportEmails( ['collaborative-service@cern.ch'] )

        Factory.getDALManager().commit()
        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def simba():
        from MaKaC.rb_factory import Factory
        from MaKaC.common.db import DBMgr
        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()


        AvatarHolder().invalidateRoomManagerIdList()


        Factory.getDALManager().commit()
        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

    @staticmethod
    def assignBookings2DanieleLajust():
        from MaKaC.rb_factory import Factory
        from MaKaC.common.db import DBMgr
        DBMgr.getInstance().startRequest()
        Factory.getDALManager().connect()

        from MaKaC.rb_room import RoomBase

        print "Connected..."

        avatar = AvatarHolder().match( { "email": "Daniele.Lajust@cern.ch" } )[0]

        resvEx = ReservationBase()
        resvEx.isConfirmed = None
        resvEx.bookedForName = "daniele lajust"

        allResvs = CrossLocationQueries.getReservations( resvExample = resvEx )
        for r in allResvs:
            r.createdBy = avatar.id
        #print len( allResvs )

        Factory.getDALManager().commit()
        Factory.getDALManager().disconnect()
        DBMgr.getInstance().endRequest()

if __name__ == '__main__':
    #Test.getNextRepeating()
    #Test.splitToPeriods()
    #Test.weekNumber()
    #Test.overlapsOn()
    #Test.statistics()
    #Test.getCollisions()
    #Test.addUsesAVC()
    Test.addLocationAVCSupportEmails()
    #Test.addNeedsAVCSupport()
    #Test.problem()
    #Test.assignBookings2DanieleLajust()
    pass
