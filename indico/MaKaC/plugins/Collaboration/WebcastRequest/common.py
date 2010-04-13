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
from MaKaC.common.PickleJar import Retrieves
from MaKaC.webinterface.common.contribFilters import PosterFilterField
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

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
    ("never", "Do not need it"),
    ("withinHours" , "Within hours"),
    ("withinDay" , "Within a day"),
    ("withinWeek" , "Within a week")
]

webcastPurpose = [
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
    
class WebcastRequestError(CSErrorBase):
    def __init__(self, operation, inner):
        CSErrorBase.__init__(self)
        self._operation = operation
        self._inner = inner
        
    @Retrieves(['MaKaC.plugins.Collaboration.WebcastRequest.common.WebcastRequestError'], 'origin')
    def getOrigin(self):
        return 'WebcastRequest'
        
    @Retrieves(['MaKaC.plugins.Collaboration.WebcastRequest.common.WebcastRequestError'],
               'operation')
    def getOperation(self):
        return self._operation
    
    @Retrieves(['MaKaC.plugins.Collaboration.WebcastRequest.common.WebcastRequestError'],
               'inner')
    def getInner(self):
        return str(self._inner)
    
    def getUserMessage(self):
        return ''
    
    def getLogMessage(self):
        return "Webcast Request error for operation: " + str(self._operation) + ", inner exception: " + str(self._inner)
    
    
class WebcastRequestException(CollaborationServiceException):
    pass