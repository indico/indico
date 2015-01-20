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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase, WCSCSSBase,\
    CollaborationTools
from MaKaC.plugins.Collaboration.RecordingRequest.common import \
    postingUrgency
from MaKaC.conference import Contribution
from MaKaC.common.timezoneUtils import isSameDay
from MaKaC.common.fossilize import fossilize
from MaKaC.common.Conversion import Conversion
from MaKaC.plugins.Collaboration.RecordingRequest.fossils import IContributionRRFossil
from MaKaC.plugins.Collaboration import urlHandlers as collaborationUrlHandlers
from MaKaC.plugins.Collaboration.RecordingRequest.common import getCommonTalkInformation
from MaKaC.plugins.Collaboration.handlers import RCCollaborationAdmin, RCCollaborationPluginAdmin
from indico.core.index import Catalog

class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        vars["IsSingleBooking"] = not CollaborationTools.getCSBookingClass(self._pluginId)._allowMultiple
        vars["Conference"] = self._conf

        isLecture = self._conf.getType() == 'simple_event'
        vars["IsLecture"] = isLecture

        underTheLimit = self._conf.getNumberOfContributions() <= self._RecordingRequestOptions["contributionLoadLimit"].getValue()
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        user = self._rh._getUser()
        isManager = user.isAdmin() or RCCollaborationAdmin.hasRights(user) or \
            RCCollaborationPluginAdmin.hasRights(user, plugins=['RecordingRequest'])
        booking = manager.getSingleBooking('RecordingRequest')
        initialChoose = booking is not None and booking._bookingParams['talks'] == 'choose'
        initialDisplay = (self._conf.getNumberOfContributions() > 0 and underTheLimit) or (booking is not None and initialChoose)


        vars["InitialChoose"] = initialChoose
        vars["DisplayTalks"] = initialDisplay
        vars["isManager"] = isManager

        talks, rRoomFullNames, rRoomNames, recordingAbleTalks, recordingUnableTalks = getCommonTalkInformation(self._conf)
        nRecordingCapable = len(recordingAbleTalks)

        vars["HasRecordingCapableTalks"] = nRecordingCapable > 0
        vars["NTalks"] = len(talks)

        # list of "locationName:roomName" strings
        vars["RecordingCapableRooms"] = rRoomFullNames
        vars["NRecordingCapableContributions"] = nRecordingCapable

        # we check if the event itself is recoring capable (depends on event's room)
        confLocation = self._conf.getLocation()
        confRoom = self._conf.getRoom()
        if confLocation and confRoom and (confLocation.getName() + ":" + confRoom.getName() in rRoomNames):
            topLevelRecordingCapable = True
        else:
            topLevelRecordingCapable = False

        # Finally, this event is recoring capable if the event itself
        # or one of its talks are capable or user is admin, collaboration
        # manager or recording plugin manager
        vars["RecordingCapable"] = topLevelRecordingCapable or nRecordingCapable > 0 or isManager

        recordingAbleTalks.sort(key = Contribution.contributionStartDateForSort)
        talks.sort(key = Contribution.contributionStartDateForSort)

        fossil_args = dict(tz=self._conf.getTimezone(),
                           units='(hours)_minutes',
                           truncate=True)

        vars["Contributions"] = fossilize(talks, IContributionRRFossil, **fossil_args)
        vars["ContributionsAble"] = fossilize(recordingAbleTalks, IContributionRRFossil, **fossil_args)
        vars["ContributionsUnable"] = fossilize(recordingUnableTalks, IContributionRRFossil, **fossil_args)

        vars["PostingUrgency"] = postingUrgency
        vars["linkToEA"] = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
        vars["agreementName"] = CollaborationTools.getOptionValue("RecordingRequest", "AgreementName")
        return vars

class WMain (WJSBase):
    pass

class WIndexing(WJSBase):
    pass

class WExtra (WJSBase):
    def getVars(self):
        vars = WJSBase.getVars( self )

        if self._conf:
            vars["ConferenceId"] = self._conf.getId()
            vars["NumberOfContributions"] = self._conf.getNumberOfContributions()

            # these 2 vars are used to see if contrib dates shown should include day or just time
            vars["ConfStartDate"] = Conversion.datetime(self._conf.getAdjustedStartDate())
            vars["IsMultiDayEvent"] = not isSameDay(self._conf.getStartDate(), self._conf.getEndDate(), self._conf.getTimezone())

            location = ""
            if self._conf.getLocation() and self._conf.getLocation().getName():
                location = self._conf.getLocation().getName().strip()
            vars["ConfLocation"] = location

            room = ""
            if self._conf.getRoom() and self._conf.getRoom().getName():
                room = self._conf.getRoom().getName().strip()
            vars["ConfRoom"] = room

        else:
            # this is so that template can still be rendered in indexes page...
            # if necessary, we should refactor the Extra.js code so that it gets the
            # conference data from the booking, now that the booking has the conference inside
            vars["ConferenceId"] = ""
            vars["NumberOfContributions"] = 0
            vars["ConfStartDate"] = ""
            vars["IsMultiDayEvent"] = False
            vars["ConfLocation"] = ""
            vars["ConfRoom"] = ""

        return vars

class WStyle (WCSCSSBase):
    pass
