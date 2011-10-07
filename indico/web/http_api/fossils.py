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

"""
Basic fossils for data export
"""

from indico.util.fossilize import IFossil, fossilize
from indico.util.fossilize.conversion import Conversion
from MaKaC.webinterface import urlHandlers
from MaKaC.fossils.conference import ISessionFossil


class IHTTPAPIErrorFossil(IFossil):
    def getMessage(self):
        pass


class IHTTPAPIResultFossil(IFossil):
    def getTS(self):
        pass
    getTS.name = 'ts'

    def getURL(self):
        pass
    getURL.name = 'url'

    def getResults(self):
        pass


class IHTTPAPIExportResultFossil(IHTTPAPIResultFossil):
    def getCount(self):
        pass

    def getComplete(self):
        pass

    def getAdditionalInfo(self):
        pass


class IPeriodFossil(IFossil):
    def startDT(self):
        pass
    startDT.convert = Conversion.datetime

    def endDT(self):
        pass
    endDT.convert = Conversion.datetime


class ICategoryMetadataFossil(IFossil):
    def getId(self):
        pass

    def getName(self):
        pass

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHCategoryDisplay)
    getLocator.name = 'url'

class ICategoryProtectedMetadataFossil(ICategoryMetadataFossil):
    def getName(self):
        pass
    getName.produce = lambda x: None


class IConferenceMetadataFossil(IFossil):

    def getId(self):
        pass

    def getStartDate(self):
        pass
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        pass
    getEndDate.convert = Conversion.datetime

    def getTitle(self):
        pass

    def getDescription(self):
        pass

    def getType(self):
        pass

    def getOwner(self):
        pass
    getOwner.convert = lambda x: x.getTitle()
    getOwner.name = 'category'

    def getCategoryId(self):
        pass
    getCategoryId.produce = lambda x: x.getOwner().getId()

    def getTimezone(self):
        pass

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = lambda l: l and l.getName()

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHConferenceDisplay)
    getLocator.name = 'url'

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = lambda r: r and r.getName()


class IContributionParticipationMetadataFossil(IFossil):

    def getId(self):
        pass

    def getFullName(self):
        pass

    def getEmail(self):
        pass

    def getAffiliation(self):
        pass


class IContributionMetadataFossil(IFossil):

    def getId(self):
        pass

    def getTitle(self):
        pass

    def getLocation(self):
        pass
    getLocation.convert = lambda l: l and l.getName()

    def getRoom(self):
        pass
    getRoom.convert = lambda r: r and r.getName()

    def getStartDate(self):
        pass
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        pass
    getEndDate.convert = Conversion.datetime

    def getDuration(self):
        pass
    getDuration.convert = Conversion.duration

    def getDescription(self):
        pass

    def getSpeakerList(self):
        pass
    getSpeakerList.name = 'speakers'
    getSpeakerList.result = IContributionParticipationMetadataFossil

    def getTrack( self ):
        pass
    getTrack.convert = lambda t: t and t.getTitle()

    def getSession( self ):
        pass
    getSession.convert = lambda s: s and s.getTitle()

    def getType(self):
        pass
    getType.convert = lambda t: t and t.getName()


class ISubContributionMetadataFossil(IFossil):

    def getId(self):
        pass

    def getTitle(self):
        pass

    def getDuration(self):
        pass
    getDuration.convert = Conversion.duration

    def getSpeakerList(self):
        pass
    getSpeakerList.name = 'speakers'
    getSpeakerList.result = IContributionParticipationMetadataFossil


class IContributionMetadataWithSubContribsFossil(IContributionMetadataFossil):

    def getSubContributionList(self):
        pass
    getSubContributionList.result = ISubContributionMetadataFossil
    getSubContributionList.name = 'subContributions'


class IConferenceMetadataWithContribsFossil(IConferenceMetadataFossil):

    def getContributionList(self):
        pass
    getContributionList.result = IContributionMetadataFossil
    getContributionList.name = 'contributions'


class IConferenceMetadataWithSubContribsFossil(IConferenceMetadataFossil):

    def getContributionList(self):
        pass
    getContributionList.result = IContributionMetadataWithSubContribsFossil
    getContributionList.name = 'contributions'


class ISessionMetadataFossil(ISessionFossil):

    def getContributionList(self):
        pass
    getContributionList.result = IContributionMetadataWithSubContribsFossil
    getContributionList.name = 'contributions'


class IConferenceMetadataWithSessionsFossil(IConferenceMetadataFossil):

    def getSessionList(self):
        pass
    getSessionList.result = ISessionMetadataFossil
    getSessionList.name = 'sessions'

    def getContributionListWithoutSessions(self):
        pass
    getContributionListWithoutSessions.result = IContributionMetadataWithSubContribsFossil
    getContributionListWithoutSessions.name = 'contributions'
