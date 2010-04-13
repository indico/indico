# -*- coding: utf-8 -*-
##
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

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers

from MaKaC.webinterface.pages.contributions import WPContributionModifBase

class WPContributionReviewing( WPContributionModifBase ):
    
    def __init__(self, rh, contribution):
        WPContributionModifBase.__init__(self, rh, contribution)
        self._aw = rh.getAW()
    
    def _setActiveTab( self ):
        self._tabReviewing.setActive()
        
    def _getTabContent( self, params ):  
        wc = WContributionReviewing(self._target.getConference(), self._aw)
        assignRefereeURL = urlHandlers.UHAssignReferee.getURL(self._target)
        removeAssignRefereeURL = urlHandlers.UHRemoveAssignReferee.getURL(self._target)
        assignEditingURL = urlHandlers.UHAssignEditing.getURL(self._target)
        removeAssignEditingURL = urlHandlers.UHRemoveAssignEditing.getURL(self._target)
        assignReviewingURL = urlHandlers.UHAssignReviewing.getURL(self._target)
        removeAssignReviewingURL = urlHandlers.UHRemoveAssignReviewing.getURL(self._target)
        finalJudgeURL = urlHandlers.UHFinalJudge.getURL(self._target)
    
        return wc.getHTML(self._target, assignRefereeURL, removeAssignRefereeURL, assignEditingURL, removeAssignEditingURL, assignReviewingURL, removeAssignReviewingURL, finalJudgeURL)

class WContributionReviewing(wcomponents.WTemplated): 
    
    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw
    
    def getHTML( self, target, assignRefereeURL, removeAssignRefereeURL, assignEditingURL, removeAssignEditingURL, assignReviewingURL, removeAssignReviewingURL, finalJudgeURL ):

        self.__target = target
        params = {"assignRefereeURL" : assignRefereeURL, \
                  "removeAssignRefereeURL" : removeAssignRefereeURL,\
                  "assignEditingURL" : assignEditingURL, \
                  "removeAssignEditingURL" : removeAssignEditingURL, \
                  "assignReviewingURL" : assignReviewingURL, \
                  "removeAssignReviewingURL" : removeAssignReviewingURL, \
                  "finalJudgeURL": finalJudgeURL}
        return wcomponents.WTemplated.getHTML(self, params)
        
    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )

        conferenceChoice = self._conf.getConfReview().getChoice()
        reviewManager = self.__target.getReviewManager()
        canAssignReferee = self._conf.getConfReview().isPaperReviewManager(self._aw.getUser()) or self._conf.canModify(self._aw)
        
        vars["Conference"] = self._conf
        vars["ConfReview"] = self._conf.getConfReview()
        vars["Contribution"] = self.__target
        vars["ConferenceChoice"] = conferenceChoice
        vars["ContributionReviewManager"] = reviewManager
        vars["CanAssignReferee"] = canAssignReferee
        vars["CanAssignEditorOrReviewers"] = reviewManager.isReferee(self._aw.getUser()) or canAssignReferee
        vars["AvailableReviewers"] =  [r for r in  self._conf.getConference().getConfReview().getReviewersList() \
                                       if r not in reviewManager.getReviewersList()]
        vars["Editing"] = reviewManager.getLastReview().getEditorJudgement()
        vars["AdviceList"] = reviewManager.getLastReview().getSubmittedReviewerJudgement()
        vars["CanEditDueDates"] = canAssignReferee
        vars["IsReferee"] = self.__target.getReviewManager().isReferee(self._rh._getUser())
        vars["Review"] = self.__target.getReviewManager().getLastReview()
        vars["TrackList"] = self._conf.getTrackList()
        
        return vars

class WPJudgeEditing( WPContributionModifBase ):
    
    def _setActiveTab( self ):
        self._tabJudgeEditing.setActive()
        
    def _getTabContent( self, params ):  
        wc = WJudgeEditing(self._target)
        return wc.getHTML(self._target)

class WJudgeEditing(wcomponents.WTemplated): 
    
    def __init__(self, contrib):
        self._contrib = contrib
    
    def getHTML( self, target):
        return wcomponents.WTemplated.getHTML(self, {})
        
    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["Contribution"] = self._contrib
        vars["ConfReview"] = self._contrib.getConference().getConfReview()
        vars["Editing"] = self._contrib.getReviewManager().getLastReview().getEditorJudgement()

        return vars

class WPGiveAdvice( WPContributionModifBase ):
        
    def _setActiveTab( self ):
        self._tabGiveAdvice.setActive()
        
    def _getTabContent( self, params ):  
        wc = WGiveAdvice(self._target, self._getAW())
        return wc.getHTML()

class WGiveAdvice(wcomponents.WTemplated):
    
    def __init__(self, contrib, aw):
        self._contrib = contrib
        self._aw = aw

    def getHTML( self):
        self.__reviewer = self._aw.getUser()
        return wcomponents.WTemplated.getHTML(self, {})
        
    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["Contribution"] = self._contrib
        vars["ConfReview"] = self._contrib.getConference().getConfReview()
        vars["Advice"] = self._contrib.getReviewManager().getLastReview().getAdviceFrom(self.__reviewer)
        
        return vars
    
class WContributionReviewingDisplay(wcomponents.WTemplated):
    """ 
    """
    
    def __init__(self, contribution):
        self._contribution = contribution
        
    def getHTML(self, params):
        return wcomponents.WTemplated.getHTML(self, params)
    
    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["Editing"] = self._contribution.getReviewManager().getLastReview().getEditorJudgement()
        vars["AdviceList"] = self._contribution.getReviewManager().getLastReview().getSubmittedReviewerJudgement()
        vars["Review"] = self._contribution.getReviewManager().getLastReview()
        vars["ConferenceChoice"] = self._contribution.getConference().getConfReview().getChoice()
        return vars
    
class WPContributionReviewingHistory(WPContributionModifBase):
    
    def _setActiveTab( self ):
        self._tabReviewingHistory.setActive()
        
    def _getTabContent( self, params ):
        wc = WContributionReviewingHistory(self._target)
        return wc.getHTML({"ShowReviewingTeam" : True})

class WContributionReviewingHistory(wcomponents.WTemplated): 
    
    def __init__(self, contribution):
        self._contribution = contribution
        self._conf = contribution.getConference()
    
    def getHTML( self, params ):

        return wcomponents.WTemplated.getHTML(self, params)
        
    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["ConferenceChoice"] = self._conf.getConfReview().getChoice()
        vars["Versioning"] = self._contribution.getReviewManager().getVersioning()

        return vars