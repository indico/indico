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

from MaKaC.common.fossilize import IFossil
from MaKaC.common.fossilize import fossilize
from MaKaC.common.Conversion import Conversion
from MaKaC.webinterface import urlHandlers
from MaKaC.fossils.conference import IMaterialMinimalFossil,\
        IConferenceParticipationFossil, IConferenceParticipationMinimalFossil
from MaKaC.fossils.contribution import IContributionParticipationTTDisplayFossil,\
    IContributionParticipationTTMgmtFossil, IContributionParticipationFossil
from MaKaC.common.contextManager import ContextManager

class ISchEntryFossil(IFossil):

    def getInitId(self):
        """ Id """
    getInitId.produce = Conversion.locatorString
    getInitId.name = "id"

    def getTitle(self):
        """ Title """

    def getDescription(self):
        """ Description """

    def getSessionCode(self):
        """ Entry Session Id """
    getSessionCode.produce = Conversion.parentSessionCode


class IBreakTimeSchEntryFossil(ISchEntryFossil):

    def getInitId(self):
        """ Id """
    # 'produce' is not to be used anywhere else than for the time table
    getInitId.produce = lambda s: Conversion.locatorString(s)+"b"+s.getId()
    getInitId.name = "id"

    def getAdjustedStartDate(self):
        """ Entry Start Date """
    getAdjustedStartDate.convert = Conversion.datetime
    getAdjustedStartDate.name = "startDate"

    def getAdjustedEndDate(self):
        """ Entry End Date """
    getAdjustedEndDate.convert = Conversion.datetime
    getAdjustedEndDate.name = "endDate"

    def getDuration(self):
        """ Entry Duration """
    getDuration.convert = Conversion.timedelta

    def getEntryType(self):
        """ Entry Type """
    getEntryType.produce = lambda s: "Break"
    getEntryType.name = 'entryType'

    def getConferenceId(self):
        """ Entry Conference id """
    getConferenceId.produce = lambda s: s.getOwner().getConference().getId()

    def getSessionId(self):
        """ Entry Session id """
    getSessionId.produce = Conversion.parentSession

    def getSessionSlotId(self):
        """ Entry Session Slot Id """
    getSessionSlotId.produce = Conversion.parentSlot

    def getRoom(self):
        """ Entry Room """
    getRoom.convert = Conversion.roomName

    def getLocation(self):
        """ Entry Location """
    getLocation.convert = Conversion.locationName

    def getColor(self):
        """ Entry Color """

    def getTextColor(self):
        """ Entry Text Color """


class IBreakTimeSchEntryMgmtFossil(IBreakTimeSchEntryFossil):

    def getScheduleEntryId(self):
        """ Entry Id """
    getScheduleEntryId.produce = lambda s: s.getId()

    def getAddress(self):
        """ Entry Address """
    getAddress.produce = lambda s: s.getLocation()
    getAddress.convert = Conversion.locationAddress

    def inheritLocation(self):
        """ Does this entry inherit the location ?"""
    inheritLocation.produce = lambda s: s.getOwnLocation() is None
    inheritLocation.name = "inheritLoc"

    def inheritRoom(self):
        """ Does this entry inherit the room ?"""
    inheritRoom.produce = lambda s: s.getOwnRoom() is None
    inheritRoom.name = "inheritRoom"


class IContribSchEntryFossil(ISchEntryFossil):

    def getUniqueId(self):
        """ Unique Id """
    getUniqueId.produce = lambda s: s.getOwner().getUniqueId()

    def getEntryType(self):
        """ Entry Type """
    getEntryType.produce = lambda s: "Contribution"

    def getSessionId(self):
        """ Entry Session Id """
    getSessionId.produce = Conversion.parentSession

    def getSessionSlotId(self):
        """ Entry Session Id """
    getSessionSlotId.produce = Conversion.parentSlot

    def getContributionId(self):
        """ Entry Contribution Id """
    getContributionId.produce = lambda s: s.getOwner().getId()

    def getDescription(self):
        """ Entry Description """
    getDescription.produce = lambda s: s.getOwner().getDescription()

    def getRoom(self):
        """ Entry Room """
    getRoom.convert = Conversion.roomName

    def getLocation(self):
        """ Entry Location """
    getLocation.convert = Conversion.locationName

    def getAdjustedStartDate(self):
        """ Entry Start Date """
    getAdjustedStartDate.convert = Conversion.datetime
    getAdjustedStartDate.name = "startDate"

    def getAdjustedEndDate(self):
        """ Entry End Date """
    getAdjustedEndDate.convert = Conversion.datetime
    getAdjustedEndDate.name = "endDate"

    def getConferenceId(self):
        """ Entry Conference id """
    getConferenceId.produce = lambda s: s.getOwner().getConference().getId()


class IContribSchEntryDisplayFossil(IContribSchEntryFossil):

    def getURL(self):
        """ Entry Display URL """
    getURL.produce = lambda s: str(urlHandlers.UHContributionDisplay.getURL(s.getOwner()))
    getURL.name = "url"

    def getPDF(self):
        """ Entry PDF URL """
    getPDF.produce = lambda s: str(urlHandlers.UHConfTimeTablePDF.getURL(s.getOwner()))
    getPDF.name = "pdf"

    def getMaterial(self):
        """ Entry Material """
    getMaterial.produce = lambda s: s.getOwner().getAllViewableMaterialList()
    getMaterial.result = IMaterialMinimalFossil

    def getPresenters(self):
        """ Entry Presenters """
    getPresenters.produce = lambda x: x.getOwner().getSpeakerList()
    getPresenters.result = IContributionParticipationTTDisplayFossil


class IContribSchEntryMgmtFossil(IContribSchEntryFossil):

    def getPresenters(self):
        """ Entry Presenters """
    getPresenters.produce = lambda x: x.getOwner().getSpeakerList()
    getPresenters.result = IContributionParticipationFossil

    def getAuthors(self):
        """ Entry Primary authors """
    getAuthors.produce = lambda x: x.getOwner().getPrimaryAuthorList()
    getAuthors.result = IContributionParticipationFossil

    def getCoauthors(self):
        """ Entry Co-Authors """
    getCoauthors.produce = lambda x: x.getOwner().getCoAuthorList()
    getCoauthors.result = IContributionParticipationFossil

    def getId(self):
        """ Default Id """
    getId.name = "scheduleEntryId"

    def getAddress(self):
        """ Entry Address """
    getAddress.produce = lambda x: x.getLocation()
    getAddress.convert = Conversion.locationAddress

    def getInheritLoc(self):
        """ Inherited Loc """
    getInheritLoc.produce = lambda x: x.getOwner().getOwnLocation() is None

    def getInheritRoom(self):
        """ Inherited Room """
    getInheritRoom.produce = lambda x: x.getOwner().getOwnRoom() is None

    def getDuration(self):
        """ Entry End Date """
    getDuration.convert = Conversion.duration

    def getKeywords(self):
        """ Entry Keywords """
    getKeywords.produce = lambda x: x.getOwner().getKeywords().split("\n") if x.getOwner().getKeywords().strip() else []

    def getBoardNumber(self):
        """ Entry board number """
    getBoardNumber.produce = lambda x: x.getOwner().getBoardNumber()

    def getContributionType(self):
        """ Entry type """
    getContributionType.produce = lambda x: x.getOwner().getType().getId() if x.getOwner().getType() else None

    def getFields(self):
        """ Entry fields """
    getFields.produce = lambda x: x.getOwner().getFields(valueonly=True)

    def getReportNumbers(self):
        """ Entry report numbers """
    getReportNumbers.produce = lambda x: Conversion.getReportNumbers(x.getOwner())


class ILinkedTimeSchEntryFossil(ISchEntryFossil):

    def getTitle(self):
        """ Title """
    getTitle.produce = lambda s: s.getOwner().getSession().getTitle()

    def getDescription(self):
        """ Entry Description """
    getDescription.produce = lambda s: s.getOwner().getSession().getDescription()

    def getSlotTitle(self):
        """ Slot Title """
    getSlotTitle.produce = lambda s: s.getOwner().getTitle()

    def getSessionId(self):
        """ Session Id """
    getSessionId.produce = lambda s: s.getOwner().getSession().getId()

    def getSessionSlotId(self):
        """ Session Slot Id """
    getSessionSlotId.produce = lambda s: s.getOwner().getId()

    def getEntryType(self):
        """ Entry Type """
    getEntryType.produce = lambda s: "Session"

    def getColor(self):
        """ Entry Background color """
    getColor.produce = lambda s: s.getOwner().getColor()

    def getTextColor(self):
        """ Entry Text color """
    getTextColor.produce = lambda s: s.getOwner().getTextColor()

    def getAdjustedStartDate(self):
        """ Entry Start Date """
    getAdjustedStartDate.convert = Conversion.datetime
    getAdjustedStartDate.name = "startDate"

    def getAdjustedEndDate(self):
        """ Entry End Date """
    getAdjustedEndDate.convert = Conversion.datetime
    getAdjustedEndDate.name = "endDate"

    def isPoster(self):
        """ Is self a Poster Session ? """
    isPoster.produce = lambda s: s.getOwner().getSession().getScheduleType() == 'poster'

    def getDuration(self):
        """ Entry Duration """
    getDuration.convert = Conversion.timedelta

    def getRoom(self):
        """ Entry Room """
    getRoom.produce = lambda s: s.getOwner().getRoom()
    getRoom.convert = Conversion.roomName

    def getLocation(self):
        """ Entry Location """
    getLocation.produce = lambda s: s.getOwner().getLocation()
    getLocation.convert = Conversion.locationName

    def getConferenceId(self):
        """ Entry Conference id """
    getConferenceId.produce = lambda s: s.getOwner().getConference().getId()

    def getContribDuration(self):
        """ Default duration for contribs """
    getContribDuration.produce = lambda s: s.getOwner().getSession().getContribDuration()
    getContribDuration.convert = Conversion.timedelta

    def getInheritLoc(self):
        """ Inherited Loc """
    getInheritLoc.produce = lambda x: x.getOwner().getOwnLocation() is None

    def getInheritRoom(self):
        """ Inherited Room """
    getInheritRoom.produce = lambda x: x.getOwner().getOwnRoom() is None

    def getUniqueId(self):
        """ Unique Id """
    getUniqueId.produce = lambda s: s.getOwner().getSession().getUniqueId()


class ILinkedTimeSchEntryDisplayFossil(ILinkedTimeSchEntryFossil):

    def getURL(self):
        """ Entry Display URL """
    getURL.produce = lambda s: str(urlHandlers.UHSessionDisplay.getURL(s.getOwner()))
    getURL.name = "url"

    def getPDF(self):
        """ Entry PDF URL """
    getPDF.produce = lambda s: str(urlHandlers.UHConfTimeTablePDF.getURL(s.getOwner()))
    getPDF.name = "pdf"

    def getEntries(self):
        """ Entries contained inside the session """
    getEntries.produce = lambda s: s.getOwner().getSchedule().getEntries()
    getEntries.result = {"MaKaC.schedule.ContribSchEntry": IContribSchEntryDisplayFossil,
                         "MaKaC.schedule.BreakTimeSchEntry": IBreakTimeSchEntryFossil}

    def getMaterial(self):
        """ Entry Material """
    getMaterial.produce = lambda s: s.getOwner().getSession().getAllMaterialList()
    getMaterial.result = IMaterialMinimalFossil

    def getConveners(self):
        """ Entry Conveners """
    getConveners.produce = lambda s: s.getOwner().getOwnConvenerList()
    getConveners.result = IConferenceParticipationMinimalFossil


class ILinkedTimeSchEntryMgmtFossil(ILinkedTimeSchEntryFossil):

    def getEntries(self):
        """ Entries contained inside the session """
    getEntries.produce = lambda s: s.getOwner().getSchedule().getEntries()
    getEntries.result = {"MaKaC.schedule.ContribSchEntry": IContribSchEntryMgmtFossil,
                         "MaKaC.schedule.BreakTimeSchEntry": IBreakTimeSchEntryMgmtFossil}

    def getConveners(self):
        """ Entry Conveners """
    getConveners.produce = lambda s: s.getOwner().getOwnConvenerList()
    getConveners.result = IConferenceParticipationFossil

    def getId(self):
        """ Default Id """
    getId.name = "scheduleEntryId"


class IConferenceScheduleDisplayFossil(IFossil):

    def getEntries(self):
        """ Schedule Entries """
    getEntries.result = {"LinkedTimeSchEntry": ILinkedTimeSchEntryDisplayFossil,
                         "BreakTimeSchEntry": IBreakTimeSchEntryFossil,
                         "ContribSchEntry": IContribSchEntryDisplayFossil}


class IConferenceScheduleMgmtFossil(IFossil):

    def getEntries(self):
        """ Schedule Entries """
    getEntries.result = {"LinkedTimeSchEntry": ILinkedTimeSchEntryMgmtFossil,
                         "BreakTimeSchEntry": IBreakTimeSchEntryMgmtFossil,
                         "ContribSchEntry": IContribSchEntryMgmtFossil}
