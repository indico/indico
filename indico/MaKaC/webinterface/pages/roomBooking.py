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

from MaKaC.common.general import *
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.rb_location import CrossLocationDB
import MaKaC.common.info as info

#import MaKaC.common.info as info
#import MaKaC.archives as archives


# 0. Base classes...
#class WPRoomBookingBase0( WPMainBase ):
#    def _getHeadContent( self ):
#        """
#        !!!! WARNING
#        If you update the following, you will need to do
#        the same update in:
#        roomBooking.py / WPRoomBookingBase0  AND
#        conferences.py / WPConfModifRoomBookingBase
#
#        For complex reasons, these two inheritance chains
#        should not have common root, so this duplication is
#        necessary evil. (In general, one chain is for standalone
#        room booking and second is for conference-context room
#        booking.)
#        """
#        baseurl = self._getBaseURL()
#        conf = Config.getInstance()
#        return """
#        <!-- Lightbox -->
#        <link rel="stylesheet" href="%s/js/lightbox/lightbox.css"> <!--lightbox.css-->
#        <script type="text/javascript" src="%s/js/lightbox/lightbox.js"></script>
#
#        <!-- Our libs -->
#        <script type="text/javascript" src="%s/js/indico/validation.js"></script>
#
#        <!-- Calendar -->
#        <link rel="stylesheet" type="text/css" href="%s/css/calendar-blue.css" />
#        <script type="text/javascript" src="%s"></script>
#        <script type="text/javascript" src="%s"></script>
#        """ % ( baseurl, baseurl, baseurl, baseurl, urlHandlers.UHJavascriptCalendar.getURL(),
#                urlHandlers.UHJavascriptCalendarSetup.getURL() )


class WPRoomBookingBase( WPMainBase ):

    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("Room Booking")

    def getJSFiles(self):
        return [ 'js/prototype/prototype.js',
                 'js/scriptaculous/scriptaculous.js' ] + \
                WPMainBase.getJSFiles(self)

    def _getHeadContent( self ):
        """
        !!!! WARNING
        If you update the following, you will need to do
        the same update in:
        roomBooking.py / WPRoomBookingBase0  AND
        conferences.py / WPConfModifRoomBookingBase

        For complex reasons, these two inheritance chains
        should not have common root, so this duplication is
        necessary evil. (In general, one chain is for standalone
        room booking and second is for conference-context room
        booking.)
        """
        baseurl = self._getBaseURL()
        return """
        <!-- Lightbox -->
        <link rel="stylesheet" href="%s/js/lightbox/lightbox.css"> <!--lightbox.css-->
        <script type="text/javascript" src="%s/js/lightbox/lightbox.js"></script>

        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js"></script>
        """ % ( baseurl, baseurl, baseurl)

    def _getSideMenu(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        self._leftMenu = wcomponents.BasicSideMenu(self._getAW().getUser() != None)

        self._showResponsible = False


        if minfo.getRoomBookingModuleActive() and CrossLocationDB.isConnected():
            self._showResponsible = ( self._getAW().getUser() != None ) and self._getAW().getUser().isResponsibleForRooms()

        self._roomsOpt = wcomponents.SideMenuSection(_("View Rooms"), \
                                        urlHandlers.UHRoomBookingSearch4Rooms.getURL() )
        self._roomSearchOpt = wcomponents.SideMenuItem(_("Search rooms"),
                                        urlHandlers.UHRoomBookingSearch4Rooms.getURL(),
                                        enabled=True)
        self._roomMapOpt = wcomponents.SideMenuItem(_("Map of rooms"),
                                        urlHandlers.UHRoomBookingMapOfRooms.getURL(),
                                        enabled=True)
        self._myRoomListOpt = wcomponents.SideMenuItem(_("My rooms"),
                                        urlHandlers.UHRoomBookingRoomList.getURL( onlyMy = True ),
                                        enabled=self._showResponsible)
        self._bookingsOpt = wcomponents.SideMenuSection(_("View Bookings"), \
                                        urlHandlers.UHRoomBookingSearch4Bookings.getURL())
        self._bookARoomOpt = wcomponents.SideMenuItem(_("Book a Room"), \
                                        urlHandlers.UHRoomBookingSearch4Rooms.getURL( forNewBooking = True ),
                                        enabled=True)
        self._bookingListSearchOpt = wcomponents.SideMenuItem(_("Search bookings"),
                                        urlHandlers.UHRoomBookingSearch4Bookings.getURL(),
                                        enabled=True)
        self._bookingListCalendarOpt = wcomponents.SideMenuItem(_("Calendar"),
                                        urlHandlers.UHRoomBookingBookingList.getURL( today = True, allRooms = True ),
                                        enabled=True)
        self._myBookingListOpt = wcomponents.SideMenuItem(_("My bookings"),
                                        urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True, autoCriteria = True ),
                                        enabled=True)
        self._myPreBookingListOpt = wcomponents.SideMenuItem(_("My PRE-bookings"),
                                        urlHandlers.UHRoomBookingBookingList.getURL( onlyMy = True, onlyPrebookings = True, autoCriteria = True ),
                                        enabled=True)
        self._usersBookings = wcomponents.SideMenuItem(_("Bookings in my rooms"),
                                        urlHandlers.UHRoomBookingBookingList.getURL( ofMyRooms = True, autoCriteria = True ),
                                        enabled=self._showResponsible)
        self._usersPrebookings = wcomponents.SideMenuItem(_("PRE-bookings in my rooms"),
                                        urlHandlers.UHRoomBookingBookingList.getURL( ofMyRooms = True, onlyPrebookings = True, autoCriteria = True ),
                                        enabled=self._showResponsible)


        self._leftMenu.addSection( self._roomsOpt )
        self._roomsOpt.addItem( self._roomSearchOpt )
        self._roomsOpt.addItem( self._roomMapOpt )
        self._roomsOpt.addItem( self._myRoomListOpt )
        self._leftMenu.addSection( self._bookingsOpt )
        self._bookingsOpt.addItem( self._bookARoomOpt )
        self._bookingsOpt.addItem( self._bookingListSearchOpt )
        self._bookingsOpt.addItem( self._bookingListCalendarOpt )
        self._bookingsOpt.addItem( self._myBookingListOpt )
        self._bookingsOpt.addItem( self._myPreBookingListOpt )
        self._bookingsOpt.addItem( self._usersBookings )
        self._bookingsOpt.addItem( self._usersPrebookings )
        return self._leftMenu

    def _isRoomBooking(self):
        return True


class WPRoomBookingWelcome( WPRoomBookingBase ):

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingWelcome()
        return wc.getHTML( params )


# 1. Searching ...

class WPRoomBookingSearch4Rooms( WPRoomBookingBase ):

    def __init__( self, rh, forNewBooking = False ):
        self._rh = rh
        self._forNewBooking = forNewBooking
        WPRoomBookingBase.__init__( self, rh )

    def _getTitle(self):
        return WPRoomBookingBase._getTitle(self) + " - " + _("Search for rooms")

    def _setCurrentMenuItem( self ):
        if self._forNewBooking:
            self._bookARoomOpt.setActive(True)
        else:
            self._roomSearchOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingSearch4Rooms( self._rh, standalone = True )
        return wc.getHTML( params )

class WPRoomBookingSearch4Bookings( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _getTitle(self):
        return WPRoomBookingBase._getTitle(self) + " - " + _("Search for bookings")

    def _setCurrentMenuItem( self ):
        self._bookingListSearchOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingSearch4Bookings( self._rh )
        return wc.getHTML( params )

class WPRoomBookingSearch4Users( WPRoomBookingBase ):
    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _getBody( self, params ):
        wc = wcomponents.WUserSelection( \
             urlHandlers.UHRoomBookingSearch4Users.getURL(),
             forceWithoutExtAuth = self._rh._forceWithoutExtAuth,
             multi = False )
        params["addURL"] = urlHandlers.UHRoomBookingRoomForm.getURL()
        return wc.getHTML( params )

# 2. List of ...

class WPRoomBookingRoomList( WPRoomBookingBase ):

    def __init__( self, rh, onlyMy = False ):
        self._rh = rh
        self._onlyMy = onlyMy
        WPRoomBookingBase.__init__( self, rh )

    def _getTitle(self):
        if self._onlyMy:
            return WPRoomBookingBase._getTitle(self) + " - " + _("My Rooms")
        else:
            return WPRoomBookingBase._getTitle(self) + " - " + _("Found rooms")

    def _setCurrentMenuItem( self ):
        if self._onlyMy:
            self._myRoomListOpt.setActive(True)
        else:
            self._bookingListSearchOpt.setActive(True)


    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingRoomList( self._rh, standalone = True )
        return wc.getHTML( params )

class WPRoomBookingBookingList( WPRoomBookingBase ):

    def __init__( self, rh, today=False, onlyMy=False, onlyPrebookings=False, onlyMyRooms=False ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _getTitle(self):
        if self._rh._today:
            return WPRoomBookingBase._getTitle(self) + " - " + _("Calendar")
        elif self._rh._onlyMy and self._rh._onlyPrebookings:
            return WPRoomBookingBase._getTitle(self) + " - " + _("My PRE-bookings")
        elif self._rh._onlyMy:
            return WPRoomBookingBase._getTitle(self) + " - " + _("My bookings")
        elif self._rh._ofMyRooms and self._rh._onlyPrebookings:
            return WPRoomBookingBase._getTitle(self) + " - " + _("PRE-bookings in my rooms")
        elif self._rh._ofMyRooms:
            return WPRoomBookingBase._getTitle(self) + " - " + _("Bookings in my rooms")
        else:
            return WPRoomBookingBase._getTitle(self) + " - " + _("Found bookings")

    def _setCurrentMenuItem( self ):
        if self._rh._today:
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
            self._bookingListSearchOpt.setActive(True)

    def _getBody( self, pars ):
        wc = wcomponents.WRoomBookingBookingList( self._rh )
        return wc.getHTML( pars )


# 3. Details of...

class WPRoomBookingRoomDetails( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _getTitle(self):
        return WPRoomBookingBase._getTitle(self) + " - " + _("Room Details")

    def _setCurrentMenuItem( self ):
        self._roomSearchOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingRoomDetails( self._rh, standalone = True )
        return wc.getHTML( params )

class WPRoomBookingRoomStats( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _setCurrentMenuItem( self ):
        self._roomSearchOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingRoomStats( self._rh, standalone = True )
        return wc.getHTML( params )

class WPRoomBookingBookingDetails( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _setCurrentMenuItem( self ):
        self._bookingListSearchOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingDetails( self._rh, standalone = True )
        return wc.getHTML( params )

# 4. New booking

class WPRoomBookingBookingForm( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _setCurrentMenuItem( self ):
        self._bookARoomOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingBookingForm( self._rh, standalone = True )
        return wc.getHTML( params )

class WPRoomBookingStatement( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingStatement( self._rh )
        return wc.getHTML( params )

class WPRoomBookingConfirmBooking( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingConfirmBooking( self._rh, standalone = True )
        return wc.getHTML( params )
