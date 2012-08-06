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
    return CollaborationTools.getCommonTalkInformation(conference, 'RecordingRequest', "recordingCapableRooms")
