# -*- coding: utf-8 -*-
##
## $Id: common.py,v 1.4 2009/04/25 13:56:17 dmartinc Exp $
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
from MaKaC.plugins.Collaboration.base import CollaborationTools
from MaKaC.common.PickleJar import Retrieves
from MaKaC.webinterface.common.contribFilters import PosterFilterField

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
    
class WebcastRequestError(CSErrorBase):
    def __init__(self, operation, inner):
        CSErrorBase.__init__(self)
        self._operation = operation
        self._inner = inner
        
    @Retrieves(['MaKaC.plugins.Collaboration.WebcastRequest.common.WebcastRequestError'],
               'operation')
    def getOperation(self):
        return self._operation
    
    @Retrieves(['MaKaC.plugins.Collaboration.WebcastRequest.common.WebcastRequestError'],
               'inner')
    def getInner(self):
        return str(self._inner)
    
    
class WebcastRequestException(CollaborationServiceException):
    pass

def getFormFields( WebcastRequestOptions,conf):
    roomObject = conf.getRoom()
    vars = {}
    vars["Conference"] = conf
    selectedTalks=[]
    booking = conf.getCSBookingManager().getSingleBooking('WebcastRequest')
    if booking:
        bookingParams = booking._bookingParams
        selectedTalks=[]
        if bookingParams['talks'] == 'choose':
            selectedTalks = bookingParams["talkSelection"]
    contributions1 = []
    contributions2 = []
    filter = PosterFilterField(conf, False, False) #To filter out the poster sesions
    noPosterContributions = [cont for cont in conf.getContributionListSortedById() if filter.satisfies(cont)]
    nContributions = len(noPosterContributions)
    vars["HasContributions"] = nContributions > 0
    webcastCapableRooms= WebcastRequestOptions["webcastCapableRooms"].getValue()

    vars["WebcastCapableRooms"]=webcastCapableRooms
    nwebcastCapableContributions = 0
    for i, contribution in enumerate(noPosterContributions):
        if(contribution.getLocation() is not None and contribution.getRoom() is not None ):
            webcastCapable= contribution.getLocation().getName() + ":" + contribution.getRoom().getName() in webcastCapableRooms
        else:
            webcastCapable = False
        if webcastCapable:
            nwebcastCapableContributions+=1
        if i <= nContributions / 2:
            contributions1.append((contribution, contribution.getId() in selectedTalks,webcastCapable))
        else:
            contributions2.append((contribution, contribution.getId() in selectedTalks,webcastCapable))
    vars["ContributionLists"] = [contributions1, contributions2]
    vars["NwebcastCapableContributions"]=nwebcastCapableContributions
    vars["NContributions"]=nContributions
    if(conf.getLocation() is not None and conf.getRoom() is not None ):
        topLevelWebcastCapable = conf.getLocation().getName()+":"+conf.getRoom().getName() \
                    in webcastCapableRooms
    else:
        topLevelWebcastCapable = False
    webcastcapable = nwebcastCapableContributions>0 \
                    or topLevelWebcastCapable
    if webcastcapable:
        vars["WebcastCapable"]= "true"    
    else:
        vars["WebcastCapable"]= "false"
    vars["LectureOptions"] = lectureOptions
    vars["TypesOfEvents"] = typeOfEvents
    vars["PostingUrgency"] = postingUrgency
    vars["WebcastPurpose"] = webcastPurpose
    vars["IntendedAudience"] = intendedAudience
    vars["SubjectMatter"] = subjectMatter
    return vars