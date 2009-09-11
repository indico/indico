# -*- coding: utf-8 -*-
##
## $Id: pages.py,v 1.8 2009/04/25 13:56:17 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase, WCSCSSBase,\
    CollaborationTools
from MaKaC.plugins.Collaboration.RecordingRequest.common import typeOfEvents,\
    postingUrgency, recordingPurpose, intendedAudience, subjectMatter, lectureOptions
from MaKaC.webinterface.common.contribFilters import PosterFilterField

class WNewBookingForm(WCSPageTemplateBase):
        
    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        
        vars["IsSingleBooking"] = not CollaborationTools.getCSBookingClass(self._pluginName)._allowMultiple
        vars["Conference"] = self._conf
        booking = self._conf.getCSBookingManager().getSingleBooking('RecordingRequest')
        
        if self._conf.getNumberOfContributions() > 0:
            underTheLimit = self._conf.getNumberOfContributions() <= self._RecordingRequestOptions["contributionLoadLimit"].getValue()
            initialDisplay = underTheLimit or (booking is not None and booking._bookingParams['talks'] == 'choose')
            vars["DisplayTalks"] = initialDisplay
            
            #a talk is defined as a non-poster contribution
            talks = []
            filter = PosterFilterField(self._conf, False, False)
            for cont in self._conf.getContributionList():
                if filter.satisfies(cont):
                    talks.append(cont)
                    if not initialDisplay:
                        break
            nTalks = len(talks)
            vars["HasTalks"] = nTalks > 0 
            
            if initialDisplay:
                talks.sort(key = lambda c: c.getId())
                    
                if booking:
                    selectedTalks = booking._bookingParams["talkSelection"]
                else:
                    selectedTalks = []
    
                contributions1 = []
                contributions2 = []
                
                for i, contribution in enumerate(talks):
                    if i < (nTalks + 1) / 2:
                        contributions1.append((contribution, contribution.getId() in selectedTalks))
                    else:
                        contributions2.append((contribution, contribution.getId() in selectedTalks))
                    
                vars["TalkLists"] = [contributions1, contributions2]
        else:
            vars["DisplayTalks"] = booking is not None and booking._bookingParams['talks'] == 'choose'
            vars["HasTalks"] = False
                
        vars["ConsentFormURL"] = self._RecordingRequestOptions["ConsentFormURL"].getValue()
        vars["LectureOptions"] = lectureOptions
        vars["TypesOfEvents"] = typeOfEvents
        vars["PostingUrgency"] = postingUrgency
        vars["RecordingPurpose"] = recordingPurpose
        vars["IntendedAudience"] = intendedAudience
        vars["SubjectMatter"] = subjectMatter
        
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

        else:
            # this is so that template can still be rendered in indexes page...
            # if necessary, we should refactor the Extra.js code so that it gets the
            # conference data from the booking, now that the booking has the conference inside
            vars["ConferenceId"] = ""
            vars["NumberOfContributions"] = 0
        
        return vars

class WStyle (WCSCSSBase):
    pass