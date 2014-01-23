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

import os
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.rb_location import CrossLocationDB, Location
from MaKaC.plugins.RoomBooking.default.room import Room
import MaKaC.common.info as info


class WPRoomBookingBase( WPMainBase ):

    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("Room Booking")

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + \
                self._includeJSPackage('Management')

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + \
            self._asset_env['roombooking_sass'].urls()

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
        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js?%d"></script>
        """ % (baseurl, os.stat(__file__).st_mtime)

    def _getSideMenu(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        self._leftMenu = wcomponents.BasicSideMenu(self._getAW().getUser() != None)

        self._showResponsible = False


        if minfo.getRoomBookingModuleActive() and CrossLocationDB.isConnected():
            self._showResponsible = \
                (self._getAW().getUser() != None) and \
                (Room.isAvatarResponsibleForRooms(self._getAW().getUser()) \
                 or self._getAW().getUser().isAdmin() \
                 or self._getAW().getUser().isRBAdmin())

        self._roomsBookingOpt = wcomponents.SideMenuSection(currentPage = urlHandlers.UHRoomBookingBookRoom.getURL() )
        self._bookRoomNewOpt = wcomponents.SideMenuItem(_("Book a Room"), \
                                        urlHandlers.UHRoomBookingBookRoom.getURL(),
                                        enabled=True)
        self._roomMapOpt = wcomponents.SideMenuItem(_("Map of rooms"),
                                        urlHandlers.UHRoomBookingMapOfRooms.getURL(),
                                        enabled=True)
        self._bookingListCalendarOpt = wcomponents.SideMenuItem(_("Calendar"),
                                        urlHandlers.UHRoomBookingBookingList.getURL( today = True, allRooms = True ),
                                        enabled=True)
        self._bookingsOpt = wcomponents.SideMenuSection(_("View My Bookings"), \
                                        urlHandlers.UHRoomBookingSearch4Bookings.getURL())
        self._bookARoomOpt = wcomponents.SideMenuItem(_("Book a Room (Old)"), \
                                        urlHandlers.UHRoomBookingSearch4Rooms.getURL( forNewBooking = True ),
                                        enabled=True)
        self._bookARoomOpt.setVisible(False)
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
        self._bookingListSearchOpt = wcomponents.SideMenuItem(_("Search bookings"),
                                        urlHandlers.UHRoomBookingSearch4Bookings.getURL(),
                                        enabled=True)
        self._blockingsOpt = wcomponents.SideMenuSection(_("Room Blocking"))
        self._usersBlockings = wcomponents.SideMenuItem(_("Blockings for my rooms"),
                                        urlHandlers.UHRoomBookingBlockingsMyRooms.getURL( filterState='pending' ),
                                        enabled=self._showResponsible)
        self._roomsOpt = wcomponents.SideMenuSection(_("View Rooms"), \
                                        urlHandlers.UHRoomBookingSearch4Rooms.getURL() )
        self._roomSearchOpt = wcomponents.SideMenuItem(_("Search rooms"),
                                        urlHandlers.UHRoomBookingSearch4Rooms.getURL(),
                                        enabled=True)
        self._myRoomListOpt = wcomponents.SideMenuItem(_("My rooms"),
                                        urlHandlers.UHRoomBookingRoomList.getURL( onlyMy = True ),
                                        enabled=self._showResponsible)

        if self._showResponsible:
            self._myBlockingListOpt = wcomponents.SideMenuItem(_("My blockings"),
                                            urlHandlers.UHRoomBookingBlockingList.getURL( onlyMine = True, onlyRecent = True ),
                                            enabled=True)
        else:
            self._myBlockingListOpt = wcomponents.SideMenuItem(_("Blockings"),
                                            urlHandlers.UHRoomBookingBlockingList.getURL( onlyRecent = True ),
                                            enabled=True)
        self._blockRooms = wcomponents.SideMenuItem(_("Block rooms"),
                                        urlHandlers.UHRoomBookingBlockingForm.getURL(),
                                        enabled=self._showResponsible)


        if self._rh._getUser().isRBAdmin():
            self._adminSect = wcomponents.SideMenuSection(_("Administration"), \
                                            urlHandlers.UHRoomBookingAdmin.getURL() )
            self._adminOpt = wcomponents.SideMenuItem(_("Administration"), \
                                            urlHandlers.UHRoomBookingAdmin.getURL() )

        self._leftMenu.addSection( self._roomsBookingOpt )
        self._roomsBookingOpt.addItem( self._bookRoomNewOpt )
        if Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable():
            self._roomsBookingOpt.addItem( self._roomMapOpt )
        self._roomsBookingOpt.addItem( self._bookingListCalendarOpt )

        self._leftMenu.addSection( self._bookingsOpt )
        self._bookingsOpt.addItem( self._bookARoomOpt )
        self._bookingsOpt.addItem( self._myBookingListOpt )
        self._bookingsOpt.addItem( self._myPreBookingListOpt )
        self._bookingsOpt.addItem( self._usersBookings )
        self._bookingsOpt.addItem( self._usersPrebookings )
        self._bookingsOpt.addItem( self._bookingListSearchOpt )
        self._leftMenu.addSection( self._blockingsOpt )
        self._blockingsOpt.addItem( self._blockRooms )
        self._blockingsOpt.addItem( self._myBlockingListOpt )
        self._blockingsOpt.addItem( self._usersBlockings )
        self._leftMenu.addSection( self._roomsOpt )
        self._roomsOpt.addItem( self._roomSearchOpt )
        self._roomsOpt.addItem( self._myRoomListOpt )
        if self._rh._getUser().isRBAdmin():
            self._leftMenu.addSection( self._adminSect )
            self._adminSect.addItem( self._adminOpt )
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

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + \
               self._includeJSPackage('RoomBooking')

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

class WPRoomBookingBookRoom( WPRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + \
               self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return WPRoomBookingBase._getTitle(self) + " - " + _("Book a Room")

    def _setCurrentMenuItem( self ):
        self._bookRoomNewOpt.setActive(True)

    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingBookRoom( self._rh )
        return wc.getHTML( params )


class WPRoomBookingMapOfRooms(WPRoomBookingBase):

    def __init__(self, rh, **params):
        self._rh = rh
        self._params = params
        WPRoomBookingBase.__init__(self, rh)

    def _getTitle(self):
        return WPRoomBookingBase._getTitle(self) + " - " + _("Map of rooms")

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingMapOfRooms(**self._params)
        return wc.getHTML(params)

class WPRoomBookingMapOfRoomsWidget(WPNotDecorated):

    def __init__(self, rh, aspects, buildings, defaultLocation, forVideoConference, roomID):
        WPNotDecorated.__init__(self, rh)
        self._aspects = aspects
        self._buildings = buildings
        self._defaultLocation = defaultLocation
        self._forVideoConference = forVideoConference
        self._roomID = roomID

    def getCSSFiles(self):
        return WPNotDecorated.getCSSFiles(self) + ['css/mapofrooms.css']

    def getJSFiles(self):
        return WPNotDecorated.getJSFiles(self) + \
               self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return WPNotDecorated._getTitle(self) + " - " + _("Map of rooms")

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingMapOfRoomsWidget(self._aspects, self._buildings, self._defaultLocation, self._forVideoConference, self._roomID)
        return wc.getHTML(params)

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
            self._roomSearchOpt.setActive(True)


    def _getBody( self, params ):
        wc = wcomponents.WRoomBookingRoomList( self._rh, standalone = True, onlyMy = self._onlyMy )
        return wc.getHTML( params )

class WPRoomBookingBookingList( WPRoomBookingBase ):

    def __init__( self, rh, today=False, onlyMy=False, onlyPrebookings=False, onlyMyRooms=False ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + \
            self._includeJSPackage('RoomBooking')

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

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + \
            self._includeJSPackage('RoomBooking')

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


class WPRoomBookingBookingDetails(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        WPRoomBookingBase.__init__(self, rh)

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingDetails(self._rh)
        return wc.getHTML(params)

# 4. New booking

class WPRoomBookingBookingForm( WPRoomBookingBase ):

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + \
               self._includeJSPackage('RoomBooking')

    def __init__( self, rh ):
        self._rh = rh
        WPRoomBookingBase.__init__( self, rh )

    def _setCurrentMenuItem( self ):
        self._bookRoomNewOpt.setActive(True)

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

class WPRoomBookingBlockingsForMyRooms(WPRoomBookingBase):

    def __init__(self, rh, roomBlocks):
        WPRoomBookingBase.__init__(self, rh)
        self._roomBlocks = roomBlocks

    def _setCurrentMenuItem( self ):
        self._usersBlockings.setActive(True)

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingBlockingsForMyRooms(self._roomBlocks)
        return wc.getHTML(params)


class WPRoomBookingBlockingDetails(WPRoomBookingBase):

    def __init__(self, rh, block):
        WPRoomBookingBase.__init__(self, rh)
        self._block = block

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingBlockingDetails(self._block)
        return wc.getHTML(params)

class WPRoomBookingBlockingList(WPRoomBookingBase):

    def __init__(self, rh, blocks):
        WPRoomBookingBase.__init__(self, rh)
        self._blocks = blocks

    def _setCurrentMenuItem( self ):
        self._myBlockingListOpt.setActive(True)

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingBlockingList(self._blocks)
        return wc.getHTML(params)


class WPRoomBookingBlockingForm(WPRoomBookingBase):

    def __init__(self, rh, block, errorMessage):
        WPRoomBookingBase.__init__(self, rh)
        self._block = block
        self._errorMessage = errorMessage

    def _setCurrentMenuItem(self):
        self._blockRooms.setActive(True)

    def _getBody(self, params):
        wc = wcomponents.WRoomBookingBlockingForm(self._block, self._errorMessage)
        return wc.getHTML(params)
