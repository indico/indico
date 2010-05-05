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

lectureOptions = [
    ("none", "None"),
    ("slides", "Slides"),
    ("chalkboard", "Chalkboard"),
    ("slidesAndChalkboard" , "Slides and Chalkboard")
]

typeOfEvents = [
    ("lecturePresentation" , "Lecture / Presentation"),
    ("courseTutorial", "Course / Tutorial"),
    ("panelDiscussion" , "Panel discussion"),
    ("noAudience", "Remote teaching or candidate interview")
]

postingUrgency = [
    ("withinHours" , "Within hours"),
    ("withinDay" , "Within a day"),
    ("withinWeek" , "Within a week")
]

recordingPurpose = [
    ("historicPreservation" , "Preservation of a historically valuable talk"),
    ("remoteParticipants" , "Dissemination to participants unable to attend in person"),
    ("trainingCourse" , "Training course"),
    ("candidateInterview" , "Candidate interview"),
    ("remoteTeaching" , "Remote teaching"),
    ("savingTravel" , "Saving money on travel"),
    ("publicOutreach" , "Public outreach")
]

intendedAudience = [
    ("collaborationMembers" , "Members of a particular collaboration or experiment"),
    ("groupMembers" , "Members of a particular section or group"),
    ("studentsGrad" , "Graduate students"),
    ("studentsUndergrad" , "Undergraduate students"),
    ("studentsHighSchool" , "High school students"),
    ("studentsElementary" , "Elementary school students"),
    ("CERNUsers" , "CERN users"),
    ("CERNStaff" , "CERN staff"),
    ("technicalPersonnel" , "Technical personnel"),
    ("teachersHighSchool" , "High school teachers"),
    ("generalPublic" , "General public")
]

subjectMatter = [
    ("physics" , "Physics"),
    ("computerScience" , "Computer Science"),
    ("engineering" , "Engineering"),
    ("safety" , "Safety"),
    ("techTraining" , "Technical Training")
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
