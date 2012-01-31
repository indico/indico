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
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.WebcastRequest.fossils import IWebcastRequestErrorFossil
from MaKaC.common.fossilize import fossilizes

def getCommonTalkInformation(conference):
    """ Returns a tuple of 3 lists:
        -List of talks (Contribution objects which are not in a Poster session)
        -List of webcast capable rooms, as a list of "locationName:roomName" strings
        -List of webcast-able talks (list of Contribution objects who take place in a webcast capable room)
    """

    #a talk is defined as a non-poster contribution
    filter = PosterFilterField(conference, False, False)
    talks = [cont for cont in conference.getContributionList() if filter.satisfies(cont)]

    #list of "locationName:roomName" strings
    webcastCapableRooms = CollaborationTools.getOptionValueRooms('WebcastRequest', "webcastCapableRooms")
    wcRoomFullNames = [r.locationName + ':' + r.getFullName() for r in webcastCapableRooms]
    wcRoomNames = [r.locationName + ':' + r.name for r in webcastCapableRooms]

    #a webcast-able talk is defined as a talk talking place in a webcast-able room
    webcastAbleTalks = []
    for t in talks:
        location = t.getLocation()
        room = t.getRoom()
        if location and room and (location.getName() + ":" + room.getName() in wcRoomNames):
            webcastAbleTalks.append(t)

    return (talks, wcRoomFullNames, wcRoomNames, webcastAbleTalks)

class WebcastRequestError(CSErrorBase): #already fossilizable
    fossilizes(IWebcastRequestErrorFossil)

    def __init__(self, operation, inner):
        CSErrorBase.__init__(self)
        self._operation = operation
        self._inner = inner

    def getOperation(self):
        return self._operation

    def getInner(self):
        return str(self._inner)

    def getUserMessage(self):
        return ''

    def getLogMessage(self):
        return "Webcast Request error for operation: " + str(self._operation) + ", inner exception: " + str(self._inner)


class WebcastRequestException(CollaborationServiceException):
    pass
