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

from datetime import datetime, timedelta

from MaKaC.common import Config
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.wcomponents import WTemplated

from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.views import WPRoomBookingBase


class WPRoomBookingBookRoom(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingBookRoom, self).__init__(rh)

    def getJSFiles(self):
        return (super(WPRoomBookingBookRoom, self).getJSFiles() +
                self._includeJSPackage('RoomBooking'))

    def _getTitle(self):
        return (super(WPRoomBookingBookRoom, self)._getTitle() +
                " - " + _("Book a Room"))

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBookRoom(self._rh).getHTML(params)


class WRoomBookingBookRoom(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingBookRoom, self).getVars()

        wvars["today"] = datetime.now()
        wvars["rooms"] = self._rh._rooms
        wvars["roomBookingBookingListURL"] = urlHandlers.UHRoomBookingBookingListForBooking.getURL(newBooking='True')

        return wvars


class WPRoomBookingBookingDetails(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingBookingDetails, self).__init__(rh)

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingDetails(self._rh).getHTML(params)


class WRoomBookingDetails(WTemplated):

    def __init__(self, rh, conference=None):
        self._rh = rh
        self._resv = rh._resv
        self._conf = conference
        self._standalone = (conference is None)

    def getVars(self):
        wvars = super(WRoomBookingDetails, self).getVars()
        wvars["standalone"] = self._standalone
        wvars["reservation"] = self._resv
        wvars["collisions"] = self._rh._collisions
        wvars["config"] = Config.getInstance()
        wvars["actionSucceeded"] = self._rh._afterActionSucceeded
        if self._rh._afterActionSucceeded:
            wvars["title"] = self._rh._title
            wvars["description"] = self._rh._description

        if self._standalone:
            wvars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            wvars["modifyBookingUH"] = urlHandlers.UHRoomBookingModifyBookingForm
            wvars["cloneURL"] = urlHandlers.UHRoomBookingCloneBooking.getURL(self._resv)
        else:
            wvars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            wvars["modifyBookingUH"] = urlHandlers.UHConfModifRoomBookingModifyBookingForm
            wvars["cloneURL"] = urlHandlers.UHConfModifRoomBookingCloneBooking.getURL(self._resv)

        wvars["bookMessage"] = "Book"
        if not self._resv.isConfirmed:
            wvars["bookMessage"] = "PRE-Book"

        return wvars


class WPRoomBookingBookingList(WPRoomBookingBase):

    def __init__(self, rh, today=False, onlyMy=False, onlyPrebookings=False, onlyMyRooms=False):
        self._rh = rh
        super(WPRoomBookingBookingList, self).__init__(rh)

    def getJSFiles(self):
        return (super(WPRoomBookingBookingList, self).getJSFiles() +
                self._includeJSPackage('RoomBooking'))

    def _getTitle(self):
        base_title = super(WPRoomBookingBookingList, self)._getTitle() + ' - '
        if self._rh._today:
            return base_title + _("Calendar")
        elif self._rh._onlyMy and self._rh._onlyPrebookings:
            return base_title + _("My PRE-bookings")
        elif self._rh._onlyMy:
            return base_title + _("My bookings")
        elif self._rh._ofMyRooms and self._rh._onlyPrebookings:
            return base_title + _("PRE-bookings in my rooms")
        elif self._rh._ofMyRooms:
            return base_title + _("Bookings in my rooms")
        else:
            return base_title + _("Found bookings")

    def _setCurrentMenuItem(self):
        if self._rh._today or self._rh._allRooms:
            self._bookingListCalendarOpt.setActive(True)
        elif self._rh._onlyMy and self._rh._onlyPrebookings:
            self._myPreBookingListOpt.setActive(True)
        elif self._rh._onlyMy:
            self._myBookingListOpt.setActive(True)
        elif self._rh._ofMyRooms and self._rh._onlyPrebookings:
            self._usersPrebookings.setActive(True)
        elif self._rh._ofMyRooms:
            self._usersBookings.setActive(True)
        else:
            self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBookingList(self._rh).getHTML(params)


class WRoomBookingBookingList(WTemplated):  # Standalone version

    def __init__(self, rh):
        self._rh = rh
        self._candResvs = rh._candResvs
        self._title = None
        try: self._title = self._rh._title;
        except: pass

    def _isOn(self, boolVal):
        if boolVal:
            return "on"
        else:
            return ""

    def getVars(self):
        wvars = super(WRoomBookingBookingList, self).getVars()
        rh = self._rh
        candResvs = self._candResvs

        wvars["finishDate"] = rh._finishDate
        wvars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        wvars["withPhoto"] = False
        wvars["title"] = self._title
        wvars["search"] = rh._search
        wvars["showRejectAllButton"] = rh._showRejectAllButton
        wvars["prebookingsRejected"] = rh._prebookingsRejected
        wvars["subtitle"] = rh._subtitle
        wvars["description"] = rh._description
        yesterday = datetime.now() - timedelta(1)
        wvars["yesterday"] = yesterday  # datetime( dm.year, dm.month, dm.day, 0, 0, 1 )
        ed = None
        sd = rh._resvEx.startDT.date()
        if rh._resvEx.endDT:
            ed = rh._resvEx.endDT.date()
        else:
            ed = sd + timedelta(7)

        if rh._ofMyRooms and not rh._rooms:
            rh._resvs = []
        # autoCriteria - dates are calculated based on the next reservation
        elif rh._autoCriteria and not rh._resvs:
            # reservation not found for the next 7 days, change search period to 30 days
            ed = sd + timedelta(30)
            rh._resvEx.startDT = datetime(sd.year, sd.month, sd.day, 0, 0)
            rh._resvEx.endDT = datetime(ed.year, ed.month, ed.day, 23, 59)
            rh._resvs = ReservationBase.getReservations(resvExample=rh._resvEx, rooms=rh._rooms)
            firstResv = ReservationBase.findSoonest(rh._resvs, afterDT=yesterday)
            if firstResv:
                # extend period to latest reservation date if necessarily
                sd = firstResv.startDT
                ed = sd + timedelta(7)

        # set the calendar dates as calculated
        calendarStartDT = datetime(sd.year, sd.month, sd.day, 0, 0)
        calendarEndDT = datetime(ed.year, ed.month, ed.day, 23, 59)

        from MaKaC.common.utils import formatDate

        if  calendarStartDT.date() == calendarEndDT.date():
            wvars["periodName"] = "day"
        else:
            wvars["periodName"] = "period"
        wvars["startD"] = formatDate(calendarStartDT)
        wvars["endD"] = formatDate(calendarEndDT)

        # Data for previous/next URLs (it's about periods, not paging)
        newParams4Previous = rh._reqParams.copy()
        newParams4Next = rh._reqParams.copy()
        if rh._reqParams.has_key('autoCriteria'):
            del newParams4Previous['autoCriteria']
            del newParams4Next['autoCriteria']
        if rh._reqParams.has_key('day'):
            del newParams4Previous['day']
            del newParams4Next['day']


        startD = calendarStartDT.date()
        endD = calendarEndDT.date()

        if endD != startD:
            period = endD - startD

            prevStartD = startD - period - timedelta(1)
            prevEndD = startD - timedelta(1)

            nextStartD = endD + timedelta(1)
            nextEndD = endD + period + timedelta(1)
        else:
            prevStartD = prevEndD = startD - timedelta(1)
            nextStartD = nextEndD = endD + timedelta(1)

        newParams4Previous['sDay'] = prevStartD.day
        newParams4Previous['sMonth'] = prevStartD.month
        newParams4Previous['sYear'] = prevStartD.year
        newParams4Previous['eDay'] = prevEndD.day
        newParams4Previous['eMonth'] = prevEndD.month
        newParams4Previous['eYear'] = prevEndD.year

        newParams4Next['sDay'] = nextStartD.day
        newParams4Next['sMonth'] = nextStartD.month
        newParams4Next['sYear'] = nextStartD.year
        newParams4Next['eDay'] = nextEndD.day
        newParams4Next['eMonth'] = nextEndD.month
        newParams4Next['eYear'] = nextEndD.year

        wvars["attributes"] = {}
        wvars["withPrevNext"] = True
        wvars["prevURL"] = urlHandlers.UHRoomBookingBookingList.getURL(newParams=newParams4Previous)
        wvars["nextURL"] = urlHandlers.UHRoomBookingBookingList.getURL(newParams=newParams4Next )

        wvars['overload'] = self._rh._overload
        wvars['dayLimit'] = self._rh._dayLimit
        wvars['newBooking'] = self._rh._newBooking

        # empty days are shown for "User bookings" and "User pre-bookings"
        # and for the calendar as well
        # but not for the booking search
        # showEmptyDays = ( self._rh._ofMyRooms or \
        #                  (not self._rh._ofMyRooms and not self._rh._onlyMy) ) and \
        #                  not self._rh._search

        showEmptyDays = showEmptyRooms = not (self._rh._newBooking or self._rh._onlyMy)

        # Calendar related stuff ==========

        bars = []
        collisionsOfResvs = []

        # Bars: Candidate reservation
        collisions = [] # only with confirmed resvs
        for candResv in candResvs:
            periodsOfCandResv = candResv.splitToPeriods()
            for p in periodsOfCandResv:
                bars.append(Bar(Collision((p.startDT, p.endDT), candResv), Bar.CANDIDATE ))

            # Bars: Conflicts all vs candidate
            candResvIsConfirmed = candResv.isConfirmed;
            candResv.isConfirmed = None

            candResv.startDT, calendarStartDT = calendarStartDT, candResv.startDT
            candResv.endDT, calendarEndDT = calendarEndDT, candResv.endDT

            allCollisions = candResv.getCollisions()

            candResv.startDT, calendarStartDT = calendarStartDT, candResv.startDT
            candResv.endDT, calendarEndDT = calendarEndDT, candResv.endDT

            candResv.isConfirmed = candResvIsConfirmed
            if candResv.id:
                # Exclude candidate vs self pseudo-conflicts (Booking modification)
                allCollisions = filter(lambda c: c.withReservation.id != candResv.id, allCollisions)
            for c in allCollisions:
                if c.withReservation.isConfirmed:
                    bars.append(Bar(c, Bar.UNAVAILABLE))
                else:
                    bars.append(Bar(c, Bar.PREBOOKED))

            allCollisions = candResv.getCollisions()

            for c in allCollisions:
                if c.withReservation.isConfirmed:
                    bars.append(Bar(c, Bar.CONFLICT))
                    collisions.append(c)
                else:
                    bars.append(Bar(c, Bar.PRECONFLICT))

            wvars["conflictsNumber"] = len(collisions)
            if not candResv.isRejected and not candResv.isCancelled:
                wvars["thereAreConflicts"] = wvars["conflictsNumber"] > 0
            else:
                wvars["thereAreConflicts"] = False

        # there's at least one reservation
        if rh._resvs > 0:

            # Prepare the list of Collisions
            # (collision is just a helper object, it's not the best notion here)

            for r in rh._resvs:
                for p in r.splitToPeriods(endDT=calendarEndDT, startDT=calendarStartDT):
                    if p.startDT >= calendarStartDT and p.endDT <= calendarEndDT:
                        collisionsOfResvs.append( Collision( ( p.startDT, p.endDT ), r ) )

            # Translate collisions to Bars
            for c in collisionsOfResvs:
                if c.withReservation.isConfirmed:
                    bars.append(Bar(c, Bar.UNAVAILABLE))
                else:
                    bars.append(Bar(c, Bar.PREBOOKED))

            bars = barsList2Dictionary(bars)
            bars = addOverlappingPrebookings(bars)
            bars = sortBarsByImportance(bars, calendarStartDT, calendarEndDT)

            rooms = set(r.room for r in rh._resvs)

            #CrossLocationQueries.getRooms( location = self.location )
            if not self._rh._onlyMy:
                rooms = self._rh._rooms

            bars = introduceRooms(rooms, bars, calendarStartDT, calendarEndDT, showEmptyDays=showEmptyDays, showEmptyRooms=showEmptyRooms, user=rh._aw.getUser())

            wvars["Bar"] = Bar

            self.__sortUsingCriterion(rh._order, collisionsOfResvs)

        # we want to display every room, with or without reservation
        else:
            # initialize collision bars
            bars = barsList2Dictionary( bars )
            bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )

            # insert rooms
            if not self._rh._onlyMy:
                rooms = self._rh._rooms
            else:
                rooms = []

            bars = introduceRooms(rooms, bars, calendarStartDT, calendarEndDT, showEmptyDays=showEmptyDays, showEmptyRooms=showEmptyRooms, user=rh._aw.getUser())


        fossilizedBars = {}
        for key in bars:
            cachedDayBars = self._rh._dayBars.get(str(key))
            if not cachedDayBars:
                fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
            else:
                fossilizedBars[str(key)] = cachedDayBars
        if self._rh._updateCache:
            self._rh._cache.set_multi(fossilizedBars, 7200)
        resvIds = set()
        for dayBars in fossilizedBars.itervalues():
            for roomBars in dayBars:
                for bar in roomBars['bars']:
                    resvIds.add(bar['forReservation']['id'])
        numResvs = len(resvIds)
        wvars["barsFossil"] = fossilizedBars
        wvars["numResvs"] = numResvs
        wvars["dayAttrs"] = fossilize({})
        wvars["showEmptyRooms"] = showEmptyRooms
        wvars["manyRooms"] = not self._rh._rooms or len(self._rh._rooms) > 1
        wvars["calendarParams"] = {}
        if self._title and rh._ofMyRooms:
            wvars["calendarParams"]["ofMyRooms"] ="on"
        elif rh._onlyMy:
            wvars["calendarParams"]["onlyMy"] = "on"
        elif rh._allRooms:
            wvars["calendarParams"]["roomGUID"] = "allRooms"
        else:
            for room in rh._roomGUIDs:
                wvars["calendarParams"]["roomGUID"]= room
        if rh._onlyPrebookings:
            wvars["calendarParams"]["onlyPrebookings"] = "on"
        if rh._onlyBookings:
            wvars["calendarParams"]["onlyBookings"] ="on"
        wvars["repeatability"] = rh._repeatability
        wvars["flexibleDatesRange"] = rh._flexibleDatesRange
        wvars["calendarFormUrl"] = urlHandlers.UHRoomBookingBookingList.getURL()
        wvars["numRooms"] = len(rh._rooms) if rh._rooms else 0
        wvars["ofMyRooms"] = rh._ofMyRooms

        return wvars


    def __sortUsingCriterion(self, order, uresvs):

        if order == "" or order =="room":
            # standard sorting order (by room, and then date)
            uresvs.sort(lambda r1,r2: cmp(r1.withReservation.room.name,r2.withReservation.room.name))
        else:
            if order == 'date':
                uresvs.sort(lambda r1, r2: cmp(r1.startDT, r2.startDT))
            elif order == 'reason':
                uresvs.sort(lambda r1, r2: cmp(r1.withReservation.reason.lower(), r2.withReservation.reason.lower()))
            elif order == 'for':
                uresvs.sort(lambda r1, r2: cmp(r1.withReservation.bookedForName.lower(), r2.withReservation.bookedForName.lower()))
            elif order == 'hours':
                uresvs.sort(lambda r1, r2: cmp(r1.startDT.time(), r2.startDT.time()))


class WPRoomBookingSearch4Bookings(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingSearch4Bookings, self).__init__(rh)

    def _getTitle(self):
        return (super(WPRoomBookingBase, self)._getTitle() +
                " - " + _("Search for bookings"))

    def _setCurrentMenuItem(self):
        self._bookingListSearchOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingSearch4Bookings(self._rh).getHTML(params)


class WRoomBookingSearch4Bookings(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingSearch4Bookings, self).getVars()

        wvars["today"] = datetime.now()
        wvars["weekLater"] = datetime.now() + timedelta(7)
        wvars["Location"] = Location
        wvars["rooms"] = self._rh._rooms
        wvars["repeatability"] = None
        wvars["isResponsibleForRooms"] = Room.isAvatarResponsibleForRooms(self._rh.getAW().getUser())
        wvars["roomBookingBookingListURL"] = urlHandlers.UHRoomBookingBookingList.getURL(None)

        return wvars


class WPRoomBookingBookingForm(WPRoomBookingBase):

    def getJSFiles(self):
        return (super(WPRoomBookingBookingForm, self).getJSFiles() +
                self._includeJSPackage('RoomBooking'))

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingBookingForm, self).__init__(rh)

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBookingForm(self._rh, standalone=True).getHTML(params)


class WRoomBookingBookingForm(WTemplated):

    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._candResv = rh._candResv
        self._standalone = standalone

    def getVars(self):
        wvars = super(WRoomBookingBookingForm, self).getVars()

        wvars["standalone"] = self._standalone
        wvars["config"] = Config.getInstance()

        if self._standalone:
            wvars["conf"] = None
            wvars["saveBookingUH"] = urlHandlers.UHRoomBookingSaveBooking
            wvars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            wvars["calendarPreviewUH"] = urlHandlers.UHRoomBookingBookingForm
            wvars["bookingFormURL"] = urlHandlers.UHRoomBookingBookingForm
        else:
            wvars["conf"] = self._rh._conf
            wvars["saveBookingUH"] = urlHandlers.UHConfModifRoomBookingSaveBooking
            wvars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            wvars["calendarPreviewUH"] = urlHandlers.UHConfModifRoomBookingBookingForm
            wvars["bookingFormURL"] = urlHandlers.UHConfModifRoomBookingBookingForm

        wvars["candResv"] = self._candResv
        wvars["startDT"] = self._candResv.startDT
        wvars["endDT"] = self._candResv.endDT
        wvars["startT"] = ''
        wvars["endT"] = ''
        if any((self._candResv.startDT.hour,
                self._candResv.startDT.minute,
                self._candResv.endDT.hour,
                self._candResv.endDT.minute)):
            wvars["startT"] = '%02d:%02d' % (self._candResv.startDT.hour, self._candResv.startDT.minute)
            wvars["endT"] = '%02d:%02d' % (self._candResv.endDT.hour, self._candResv.endDT.minute)

        wvars["showErrors"] = self._rh._showErrors
        wvars["errors"] = self._rh._errors
        wvars["thereAreConflicts"] = self._rh._thereAreConflicts
        wvars["skipConflicting"] = self._rh._skipConflicting

        if self._rh._formMode == FormMode.MODIF:
            wvars["allowPast"] = "true"
        else:
            wvars["allowPast"] = "false"
        wvars["formMode"] = self._rh._formMode
        wvars["FormMode"] = FormMode

        # [Book] or [PRE-Book] ?
        bookingMessage = "Book"
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook( user ) and not room.canBook( user ):
            bookingMessage = "PRE-Book"
        wvars["bookingMessage"] = bookingMessage
        wvars["user"] = user

        if self._rh._formMode != FormMode.MODIF:
            bText = bookingMessage
        else:
            bText = "Save"

        wvars["roomBookingRoomCalendar"] = WRoomBookingRoomCalendar(self._rh, self._standalone, buttonText=bText).getHTML({})
        wvars["rooms"] = self._rh._rooms
        wvars["infoBookingMode"] = self._rh._infoBookingMode

        return wvars


class WRoomBookingRoomCalendar(WTemplated):

    def __init__( self, rh, standalone = False, buttonText ='' ):
        self._rh = rh
        self._candResv = rh._candResv
        self._standalone = standalone
        self._buttonText = buttonText

    def getVars( self ):
        vars = WTemplated.getVars( self )

        candResv = self._candResv
        room = candResv.room

        if self._standalone:
            vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            vars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails

        # Calendar range
        now = datetime.now()
        if candResv != None: #.startDT != None and candResv.endDT != None:
            calendarStartDT = datetime( candResv.startDT.year, candResv.startDT.month, candResv.startDT.day, 0, 0, 1 )  # Potential performance problem
            calendarEndDT =  datetime( candResv.endDT.year, candResv.endDT.month, candResv.endDT.day, 23, 59 )     # with very long reservation periods
        else:
            calendarStartDT = datetime( now.year, now.month, now.day, 0, 0, 1 )
            calendarEndDT = calendarStartDT + timedelta( 3 * 31, 50, 0, 0, 59, 23 )

        # example resv. to ask for other reservations
        resvEx = CrossLocationFactory.newReservation( location = room.locationName )
        resvEx.startDT = calendarStartDT
        resvEx.endDT = calendarEndDT
        resvEx.repeatability = RepeatabilityEnum.daily
        resvEx.room = room
        resvEx.isConfirmed = None # To include both confirmed and not confirmed

        # Bars: Existing reservations
        collisionsOfResvs = resvEx.getCollisions()
        bars = []
        for c in collisionsOfResvs:
            if c.withReservation.isConfirmed:
                bars.append( Bar( c, Bar.UNAVAILABLE ) )
            else:
                bars.append( Bar( c, Bar.PREBOOKED ) )

        # Bars: Candidate reservation
        periodsOfCandResv = candResv.splitToPeriods()
        for p in periodsOfCandResv:
            bars.append( Bar( Collision( (p.startDT, p.endDT), candResv ), Bar.CANDIDATE  ) )

        # Bars: Conflicts all vs candidate
        candResvIsConfirmed = candResv.isConfirmed;
        candResv.isConfirmed = None
        allCollisions = candResv.getCollisions()
        candResv.isConfirmed = candResvIsConfirmed
        if candResv.id:
            # Exclude candidate vs self pseudo-conflicts (Booking modification)
            allCollisions = filter( lambda c: c.withReservation.id != candResv.id, allCollisions )
        collisions = [] # only with confirmed resvs
        for c in allCollisions:
            if c.withReservation.isConfirmed:
                bars.append( Bar( c, Bar.CONFLICT ) )
                collisions.append( c )
            else:
                bars.append( Bar( c, Bar.PRECONFLICT ) )

        if not candResv.isRejected and not candResv.isCancelled:
            vars["thereAreConflicts"] = len( collisions ) > 0
        else:
            vars["thereAreConflicts"] = False
        vars["conflictsNumber"] = len( collisions )

        bars = barsList2Dictionary( bars )
        bars = addOverlappingPrebookings( bars )
        bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )

        if not self._standalone:
            for dt in bars.iterkeys():
                for bar in bars[dt]:
                    bar.forReservation.setOwner( self._rh._conf )

        vars["blockConflicts"] = candResv.getBlockingConflictState(self._rh._aw.getUser())

        vars["calendarStartDT"] = calendarStartDT
        vars["calendarEndDT"] = calendarEndDT
        bars = introduceRooms( [room], bars, calendarStartDT, calendarEndDT, user = self._rh._aw.getUser() )
        fossilizedBars = {}
        for key in bars:
            fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
        vars["barsFossil"] = fossilizedBars
        vars["dayAttrs"] = fossilize(dict((day.strftime("%Y-%m-%d"), getDayAttrsForRoom(day, room)) for day in bars.iterkeys()))
        vars["bars"] = bars
        vars["iterdays"] = iterdays
        vars["day_name"] = day_name
        vars["Bar"] = Bar
        vars["room"] = room
        vars["buttonText"] = self._buttonText
        vars["currentUser"] = self._rh._aw.getUser()
        vars["withConflicts"] = True

        return vars


class WPRoomBookingConfirmBooking(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingConfirmBooking, self).__init__(rh)

    def _getBody(self, params):
        return WRoomBookingConfirmBooking(self._rh, standalone=True).getHTML(params)


class WRoomBookingConfirmBooking(WRoomBookingBookingForm):

    def getVars(self):
        wvars = super(WRoomBookingConfirmBooking, self).getVars()

        wvars["candResv"] = self._candResv

        wvars["standalone"] = self._standalone
        wvars["formMode"] = self._rh._formMode
        wvars["FormMode"] = FormMode
        wvars["collisions"] = self._rh._collisions

        # If we are here, we are either in booking mode and trying to overwrite PRE-Bookings...
        bookingMessage = "Book"
        bookingMessageOther = "PRE-Book"
        wvars["rejectOthers"] = True
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook( user ) and not room.canBook( user ):
            # ...or we are in PRE-booking mode and conflicting with another PRE-Booking
            bookingMessage = "PRE-Book"
            bookingMessageOther = "PRE-Book"
            wvars["rejectOthers"] = False
        wvars["bookingMessage"] = bookingMessage
        wvars["bookingMessageOther"] = bookingMessageOther

        if self._standalone:
            wvars["conf"] = None
            wvars["saveBookingUH"] = urlHandlers.UHRoomBookingSaveBooking
            wvars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
        else:
            wvars["conf"] = self._rh._conf
            wvars["saveBookingUH"] = urlHandlers.UHConfModifRoomBookingSaveBooking
            wvars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
        return wvars


class WPRoomBookingStatement(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingStatement, self).__init__(rh)

    def _getBody(self, params):
        return WRoomBookingStatement(self._rh).getHTML(params)


class WRoomBookingStatement(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingStatement, self).getVars()
        wvars['title'] = self._rh._title
        wvars['description'] = self._rh._description
        return wvars


class WRoomBookingList( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._standalone = standalone
        self._rh = rh
        if not standalone:
            self._conf = rh._conf

    def getVars( self ):
        vars=WTemplated.getVars( self )

        vars["reservations"] = self._rh._resvs
        vars["standalone"] = self._standalone
        dm = datetime.now() - timedelta( 1 )
        vars["yesterday"] = dm #datetime( dm.year, dm.month, dm.day, 0, 0, 1 )

        if self._standalone:
            vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            vars["conference"] = self._conf
            vars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails

        return vars

