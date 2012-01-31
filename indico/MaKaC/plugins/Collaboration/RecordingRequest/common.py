# -*- coding: utf-8 -*-
##
##
## This file is par{t of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.plugins.Collaboration.base import CollaborationServiceException,\
    CSErrorBase
from MaKaC.webinterface.common.contribFilters import PosterFilterField
from MaKaC.conference import Contribution
from MaKaC.common.fossilize import fossilizes
from MaKaC.plugins.Collaboration.RecordingRequest.fossils import IRecordingRequestErrorFossil
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

from indico.util.i18n import L_

postingUrgency = [
    ("withinHours" , L_("Within hours")),
    ("withinDay" , L_("Within a day")),
    ("withinWeek" , L_("Within a week"))
]

def getTalks(conference, oneIsEnough = False, sort = False):
    """ oneIsEnough: the algorithm will stop at the first contribution found
                     it will then return a list with a single element
        sort: if True, contributions are sorted by start date (non scheduled contributions at the end)
    """
    talks = []
    filter = PosterFilterField(conference, False, False)
    for cont in conference.getContributionList():
        if filter.satisfies(cont):
            talks.append(cont)
            if oneIsEnough:
                break
    if sort and not oneIsEnough:
        talks.sort(key = Contribution.contributionStartDateForSort)

    return talks

class RecordingRequestError(CSErrorBase): #already Fossilizable
    fossilizes(IRecordingRequestErrorFossil)

    def __init__(self, operation, inner):
        self._operation = operation
        self._inner = inner

    def getOperation(self):
        return self._operation

    def getInner(self):
        return str(self._inner)

    def getUserMessage(self):
        return ''

    def getLogMessage(self):
        return "Recording Request error for operation: " + str(self._operation) + ", inner exception: " + str(self._inner)


class RecordingRequestException(CollaborationServiceException):
    pass

def getCommonTalkInformation(conference):
    """ Returns a tuple of 3 lists:
        -List of talks (Contribution objects which are not in a Poster session)
        -List of record capable rooms, as a list of "locationName:roomName" strings
        -List of record-able talks (list of Contribution objects who take place in a record capable room)
    """

    #a talk is defined as a non-poster contribution
    filter = PosterFilterField(conference, False, False)
    talks = [cont for cont in conference.getContributionList() if filter.satisfies(cont)]

    #list of "locationName:roomName" strings
    recordingCapableRooms = CollaborationTools.getOptionValueRooms('RecordingRequest', "recordingCapableRooms")
    rRoomFullNames = [r.locationName + ':' + r.getFullName() for r in recordingCapableRooms]
    rRoomNames = [r.locationName + ':' + r.name for r in recordingCapableRooms]
    #a webcast-able talk is defined as a talk talking place in a webcast-able room
    recordingAbleTalks = []
    for t in talks:
        location = t.getLocation()
        room = t.getRoom()
        if location and room and (location.getName() + ":" + room.getName() in rRoomNames):
            recordingAbleTalks.append(t)

    return (talks, rRoomFullNames, rRoomNames, recordingAbleTalks)
