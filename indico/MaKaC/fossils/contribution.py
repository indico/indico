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
from MaKaC.common.Conversion import Conversion
from MaKaC.fossils.subcontribution import ISubContributionFossil
from MaKaC.fossils.reviewing import IReviewManagerFossil
from MaKaC.webinterface import urlHandlers


class IContributionFossil(IFossil):

    def getId(self):
        pass

    def getContributionId(self):
        pass
    getContributionId.produce = lambda l: l.getId()

    def getConferenceId(self):
        pass
    getConferenceId.produce = lambda l: l.getConference().getId()

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

    def getReviewManager(self):
        pass
    getReviewManager.result = IReviewManagerFossil

    def getTrack(self):
        pass
    getTrack.convert = lambda t: t and t.getTitle()

    def getSession(self):
        pass
    getSession.convert = lambda s: s and s.getTitle()

    def getType(self):
        pass
    getType.convert = lambda t: t and t.getName()

    def getAddress(self):
        pass
    getAddress.produce = lambda s: s.getLocation()
    getAddress.convert = Conversion.locationAddress

    def getProtectionURL(self):
        """Contribution protection URL"""
    getProtectionURL.produce = lambda s: str(urlHandlers.UHContribModifAC.getURL(s))


class IContributionParticipationTTDisplayFossil(IFossil):
    """
    Minimal Fossil for Contribution Participation to be
    used by the timetable display
    """
    def getAffiliation(self):
        pass

    def getDirectFullName(self):
        pass
    getDirectFullName.name = "name"

    def getEmail(self):
        pass

    def getFirstName(self):
        pass

    def getFamilyName(self):
        pass


class IContributionParticipationTTMgmtFossil(IFossil):
    """
    Minimal Fossil for Contribution Participation to be
    used by the timetable management
    """

    def getId(self):
        pass

    def getDirectFullName(self):
        pass
    getDirectFullName.name = "name"


class IContributionParticipationMinimalFossil(IFossil):

    def getId(self):
        pass

    def getAffiliation(self):
        pass

    def getDirectFullName(self):
        pass
    getDirectFullName.name = "name"

    def isSubmitter(self):
        pass


class IContributionParticipationFossil(IContributionParticipationMinimalFossil):

    def getURL(self):
        """ Author Display URL """
    getURL.produce = lambda s: str(urlHandlers.UHContribAuthorDisplay.getURL(s))
    getURL.name = "url"

    def getTitle(self):
        pass

    def getFirstName(self):
        pass

    def getFamilyName(self):
        pass

    def getEmail(self):
        pass

    def getAffiliation(self):
        pass

    def getAddress(self):
        pass

    def getPhone(self):
        pass

    def getFax(self):
        pass


class IContributionWithSpeakersFossil(IContributionFossil):

    def getSpeakerList(self):
        pass
    getSpeakerList.result = IContributionParticipationMinimalFossil
    getSpeakerList.name = "presenters"


class IContributionWithSubContribsFossil(IContributionFossil):

    def getSubContributionList(self):
        pass
    getSubContributionList.result = ISubContributionFossil
