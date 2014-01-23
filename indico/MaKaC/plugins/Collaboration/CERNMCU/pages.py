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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase,\
    WCSCSSBase
from MaKaC.common.utils import formatDateTime, validIP
from MaKaC.webinterface.common.tools import strip_ml_tags, unescape_html
from MaKaC.plugins.Collaboration.CERNMCU.common import getCERNMCUOptionValueByName,\
    RoomWithH323, getMinStartDate, getMaxEndDate
from MaKaC.rb_location import CrossLocationQueries, CrossLocationDB
from MaKaC.errors import MaKaCError
from MaKaC.common.logger import Logger
from MaKaC.common import info
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.pages import WAdvancedTabBase
from datetime import timedelta

class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        vars["EventTitle"] = self._conf.getTitle()
        vars["EventDescription"] = unescape_html(strip_ml_tags( self._conf.getDescription())).strip()
        vars["DefaultStartDate"] = formatDateTime(self._conf.getAdjustedStartDate() - timedelta(0, 0, 0, 0, getCERNMCUOptionValueByName("defaultMinutesBefore")))
        vars["DefaultEndDate"] = formatDateTime(self._conf.getAdjustedEndDate() + timedelta(0, 0, 0, 0, getCERNMCUOptionValueByName("defaultMinutesAfter")))
        vars["MinStartDate"] = formatDateTime(self._conf.getAdjustedStartDate())
        vars["MaxEndDate"] = formatDateTime(self._conf.getAdjustedEndDate())

        return vars

class WAdvancedTab(WAdvancedTabBase):

    def getVars(self):
        variables = WAdvancedTabBase.getVars(self)
        return variables

class WMain (WJSBase):

    def getVars(self):
        vars = WJSBase.getVars( self )

        vars["MinStartDate"] = formatDateTime(getMinStartDate(self._conf))
        vars["MaxEndDate"] = formatDateTime(getMaxEndDate(self._conf))
        vars["ExtraMinutesBefore"] = getCERNMCUOptionValueByName("extraMinutesBefore")
        vars["ExtraMinutesAfter"] = getCERNMCUOptionValueByName("extraMinutesAfter")

        # Code to retrieve the event's location and room in order to include the event's room
        # as an initial participant
        location = self._conf.getLocation()
        room = self._conf.getRoom()
        if location and room and location.getName() and room.getName() and location.getName().strip() and room.getName().strip():
            locationName = location.getName()
            roomName = room.getName()

            vars["IncludeInitialRoom"] = True
            vars["IPRetrievalResult"] = -1 # 0 = OK, 1 = room without H323 IP, 2 = room with invalid H323 IP, 3 = connection to RB problem, 4 = another unknown problem
            vars["InitialRoomName"] = roomName
            if self._conf.getLocation():
                vars["InitialRoomInstitution"] = locationName
            else:
                vars["InitialRoomInstitution"] = ""

            # TODO: get IP of room from a plugin option instead of querying RB DB every time
            try:
                minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
                if minfo.getRoomBookingModuleActive():
                    Logger.get("CERNMCU").info("Connecting with Room Booking DB to get a room's H323 IP")
                    CrossLocationDB.connect()
                    Logger.get("CERNMCU").info("Connection successful")

                    attName = getCERNMCUOptionValueByName("H323_IP_att_name")

                    try:
                        returnedRooms = CrossLocationQueries.getRooms( location = locationName, roomName = roomName )

                        if isinstance(returnedRooms, list):
                            if len(returnedRooms) == 0:
                                returnedRoom = None
                            else:
                                returnedRoom = returnedRooms[0]
                        else:
                            returnedRoom = returnedRooms

                        if returnedRoom != None:
                            vars["InitialRoomName"] = returnedRoom.getFullName()
                            if attName in returnedRoom.customAtts:
                                initialRoomIp = returnedRoom.customAtts[attName]
                                if (initialRoomIp.strip() == ""):
                                    initialRoomIp = "Please enter IP."
                                    vars["IPRetrievalResult"] = 1
                                elif not validIP(initialRoomIp):
                                    vars["IPRetrievalResult"] = 2
                                else:
                                    vars["IPRetrievalResult"] = 0

                            else:
                                initialRoomIp = "IP not defined for this room."
                                vars["IPRetrievalResult"] = 1

                        else:
                            initialRoomIp = "Please enter IP."
                            vars["IPRetrievalResult"] = 1

                    except AttributeError:
                        #CrossLocationQueries.getRooms fails because it does not handle location names that are not in the DB
                        initialRoomIp = "Please enter IP"
                        vars["IPRetrievalResult"] = 1
                    except Exception, e:
                        initialRoomIp = "IP not found."
                        vars["IPRetrievalResult"] = 4
                        Logger.get("CERNMCU").warning("Location: " + locationName + "Problem with CrossLocationQueries when retrieving the list of all rooms with a H323 IP: " + str(e))
                else:
                    initialRoomIp = "Please enter IP"
                    vars["IPRetrievalResult"] = 3
                    Logger.get("CERNMCU").info("Tried to retrieve a room's H323 IP, but Room Booking module was not active.")

            except MaKaCError, e:
                initialRoomIp = "IP not found."
                vars["IPRetrievalResult"] = 4
                Logger.get("CERNMCU").warning("Location: " + locationName + "MaKaCError when retrieving a room's H.323 IP: " + e.getMessage())
            except Exception, e:
                initialRoomIp = "IP not found."
                vars["IPRetrievalResult"] = 4
                Logger.get("CERNMCU").warning("Location: " + locationName + "Exception when retrieving a room's H.323 IP: " + str(e))


            vars["InitialRoomIP"] = initialRoomIp

        else:
            vars["IncludeInitialRoom"] = False
            vars["IPRetrieved"] = False
            vars["InitialRoomName"] = ""
            vars["InitialRoomInstitution"] = ""
            vars["InitialRoomIP"] = ""

        vars["CERNGatekeeperPrefix"] = getCERNMCUOptionValueByName("CERNGatekeeperPrefix")
        vars["GDSPrefix"] = getCERNMCUOptionValueByName("GDSPrefix")
        vars["MCU_IP"] = getCERNMCUOptionValueByName("MCU_IP")
        vars["Phone_number"] = getCERNMCUOptionValueByName("Phone_number")

        return vars

class WIndexing(WJSBase):
    pass

class WExtra (WJSBase):
    def getVars(self):
        vars = WJSBase.getVars( self )

        roomsWithH323IP = []

        if self._conf:

            vars["ConferenceId"] = self._conf.getId()

            # Code to get a list of H.323 Videoconference-able rooms
            # by querying Indico's RB database
            location = self._conf.getLocation()

            if location and location.getName():
                locationName = location.getName()

                # TODO: get list of room from a plugin option instead of querying the RB DB everytime
                try:
                    minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
                    if minfo.getRoomBookingModuleActive():
                        Logger.get("CERNMCU").info("Connecting with Room Booking DB to get the list of all rooms with a H323 IP")
                        CrossLocationDB.connect()
                        Logger.get("CERNMCU").info("Connection successful")

                        attName = getCERNMCUOptionValueByName("H323_IP_att_name")

                        try:
                            returnedRooms = CrossLocationQueries.getRooms( location = locationName,
                                                                           customAtts = [{"name":attName, "allowEmpty":False,
                                                                                          "filter": (lambda ip: validIP(ip))}] )
                            if not isinstance(returnedRooms, list):
                                if returnedRooms:
                                    returnedRooms = [returnedRooms]
                                else:
                                    returnedRooms = []

                            for room in returnedRooms:
                                roomsWithH323IP.append(RoomWithH323(locationName, room.getFullName(), room.customAtts[attName]))

                        except AttributeError:
                            #CrossLocationQueries.getRooms fails because it does not handle location names that are not in the DB
                            pass
                        except Exception, e:
                            Logger.get("CERNMCU").warning("Location: " + locationName + "Problem with CrossLocationQueries when retrieving the list of all rooms with a H323 IP: " + str(e))

                except MaKaCError, e:
                    Logger.get("CERNMCU").warning("Location: " + locationName + "MaKaCError when retrieving the list of all rooms with a H323 IP: " + e.getMessage())
                except Exception, e:
                    Logger.get("CERNMCU").warning("Location: " + locationName + "Exception when retrieving the list of all rooms with a H323 IP: " + str(e))
        else:
            vars["ConferenceId"] = ""

        roomsWithH323IP.sort(key = lambda room: room.getLocation()+':'+room.getName())
        vars["RoomsWithH323IP"] = roomsWithH323IP
        return vars

class WStyle (WCSCSSBase):
    pass

class WInformationDisplay(WCSPageTemplateBase):

    def __init__(self, booking, displayTz):
        WCSPageTemplateBase.__init__(self, booking.getConference(), 'CERNMCU', None)
        self._booking = booking
        self._displayTz = displayTz

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        vars["Booking"] = self._booking

        vars["CERNGatekeeperPrefix"] = getCERNMCUOptionValueByName("CERNGatekeeperPrefix")
        vars["GDSPrefix"] = getCERNMCUOptionValueByName("GDSPrefix")
        vars["MCU_IP"] = getCERNMCUOptionValueByName("MCU_IP")
        vars["Phone_number"] = getCERNMCUOptionValueByName("Phone_number")

        return vars


class XMLGenerator(object):

    @classmethod
    def getDisplayName(cls):
        return _("MCU Conference")

    @classmethod
    def getFirstLineInfo(cls, booking, displayTz):
        return booking._bookingParams["name"]

    @classmethod
    def getCustomBookingXML(cls, booking, displayTz, out):

        out.writeTag("firstLineInfo", booking._bookingParams["name"])
        out.openTag("information")

        out.openTag("section")
        out.writeTag("title", _('Name:'))
        out.writeTag("line", booking._bookingParams["name"])
        out.closeTag("section")

        if booking.getHasPin():
            out.openTag("section")
            out.writeTag("title", _('Meeting PIN:'))

            if booking.getBookingParamByName("displayPin"):
                out.writeTag("line", str(booking.getPin()))
            else:
                out.writeTag("line", _('This conference is protected by a PIN.'))

            out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Description:'))
        out.writeTag("line", booking._bookingParams["description"])
        out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Participants:'))
        if booking.getParticipantList():
            for p in booking.getParticipantList():
                out.writeTag("line", p.getDisplayName())
        else:
            out.writeTag("line", _("No participants yet"))
        out.closeTag("section")

        bookingIdInMCU = str(booking._bookingParams["id"])
        out.openTag("section")
        out.writeTag("title", _("How to join:"))
        out.writeTag("line", "".join([
            _( '1) If you are registered in the CERN Gatekeeper, please dial '),
            getCERNMCUOptionValueByName("CERNGatekeeperPrefix"),
            bookingIdInMCU
        ]))
        out.writeTag("line", "".join([
            _('2) If you have GDS enabled in your endpoint, please call '),
            getCERNMCUOptionValueByName("GDSPrefix"),
            bookingIdInMCU
        ]))
        out.writeTag("line", "".join([
            _('3) Otherwise dial '),
            getCERNMCUOptionValueByName("MCU_IP"),
            _(' and using FEC (Far-End Controls) with your remote, enter "'),
            bookingIdInMCU,
            _('" followed by the "#".')
        ]))
        out.writeTag("line", "".join([
            _('4) To join by phone dial '),
            getCERNMCUOptionValueByName("Phone_number"),
            _(' enter "'),
            bookingIdInMCU,
            _('" followed by the "#".')
        ]))
        out.closeTag("section")

        out.closeTag("information")


class ServiceInformation(object):

    @classmethod
    def getDisplayName(cls):
        return _("MCU Conference")

    @classmethod
    def getFirstLineInfo(cls, booking, displayTz=None):
        return booking._bookingParams["name"]

    @classmethod
    def getLaunchInfo(cls, booking, displayTz=None):
        return {}

    @classmethod
    def getInformation(cls, booking, displayTz=None):
        sections = []
        sections.append({
            'title' : _('Name:'),
            'lines' : [booking._bookingParams["name"]],
        })
        if booking.getHasPin():
            pinSection = {}
            pinSection['title'] = _('Meeting PIN:')
            if booking.getBookingParamByName("displayPin"):
                pinSection['lines'] = [str(booking.getPin())]
            else:
                pinSection['lines'] = [_('This conference is protected by a PIN.')]
            sections.append(pinSection)
        sections.append({
            'title' : _('Description:'),
            'lines' : [booking._bookingParams["description"]],
        })
        participantsSection = {}
        participantsSection['title'] = _('Participants:')
        participantsLines = []
        if booking.getParticipantList():
            for p in booking.getParticipantList():
                participantsLines.append(p.getDisplayName())
        else:
            participantsLines.append(_("No participants yet"))
        participantsSection['lines'] = participantsLines
        sections.append(participantsSection)

        bookingIdInMCU = str(booking._bookingParams["id"])
        howtoSection = {}
        howtoSection['title'] = _("How to join:")
        howtoSection['lines'] = [
            "".join([_( '1) If you are registered in the CERN Gatekeeper, please dial '),
                     getCERNMCUOptionValueByName("CERNGatekeeperPrefix"), bookingIdInMCU]),
            "".join([_('2) If you have GDS enabled in your endpoint, please call '),
                     getCERNMCUOptionValueByName("GDSPrefix"), bookingIdInMCU]),
            "".join([_('3) Otherwise dial '), getCERNMCUOptionValueByName("MCU_IP"),
                     _(' and using FEC (Far-End Controls) with your remote, enter "'),
                     bookingIdInMCU, _('" followed by the "#".')]),
            "".join([_('4) To join by phone dial '), getCERNMCUOptionValueByName("Phone_number"),
                     _(' enter "'), bookingIdInMCU, _('" followed by the "#".')])
        ]
        sections.append(howtoSection)
        return sections
