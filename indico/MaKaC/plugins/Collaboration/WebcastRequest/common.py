# -*- coding: utf-8 -*-
##
##
## This file is par{t of CDS Indico.
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
    webcastCapableRooms = CollaborationTools.getOptionValue('WebcastRequest', "webcastCapableRooms")

    #a webcast-able talk is defined as a talk talking place in a webcast-able room
    webcastAbleTalks = []
    for t in talks:
        location = t.getLocation()
        room = t.getRoom()
        if location and room and (location.getName() + ":" + room.getName() in webcastCapableRooms):
            webcastAbleTalks.append(t)

    return (talks, webcastCapableRooms, webcastAbleTalks)

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
