# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from indico.web.flask.util import url_for

import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.pages.contributions import WPContributionModifBase


class WPContributionReviewing( WPContributionModifBase ):

    def __init__(self, rh, contribution):
        WPContributionModifBase.__init__(self, rh, contribution)
        self._aw = rh.getAW()

    def _setActiveTab( self ):
        self._subtabReviewing.setActive()

    def _getTabContent( self, params ):
        wc = WContributionReviewing(self._conf, self._aw)
        assignRefereeURL = url_for('event_mgmt.contributionReviewing-assignReferee', self._target)
        removeAssignRefereeURL = url_for('event_mgmt.contributionReviewing-removeAssignReferee', self._target)
        assignEditingURL = url_for('event_mgmt.contributionReviewing-assignEditing', self._target)
        removeAssignEditingURL = url_for('event_mgmt.contributionReviewing-removeAssignEditing', self._target)
        assignReviewingURL = url_for('event_mgmt.contributionReviewing-assignReviewing', self._target)
        removeAssignReviewingURL = url_for('event_mgmt.contributionReviewing-removeAssignReviewing', self._target)

        return wc.getHTML(self._target, assignRefereeURL, removeAssignRefereeURL, assignEditingURL, removeAssignEditingURL, assignReviewingURL, removeAssignReviewingURL)

class WContributionReviewing(wcomponents.WTemplated):

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw

    def getHTML( self, target, assignRefereeURL, removeAssignRefereeURL, assignEditingURL, removeAssignEditingURL, assignReviewingURL, removeAssignReviewingURL ):

        self.__target = target
        params = {"assignRefereeURL" : assignRefereeURL, \
                  "removeAssignRefereeURL" : removeAssignRefereeURL,\
                  "assignEditingURL" : assignEditingURL, \
                  "removeAssignEditingURL" : removeAssignEditingURL, \
                  "assignReviewingURL" : assignReviewingURL, \
                  "removeAssignReviewingURL" : removeAssignReviewingURL}
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )
        review_manager = self._conf.getReviewManager(self.__target)

        conferenceChoice = self._conf.getConfPaperReview().getChoice()
        conferenceChoiceStr = self._conf.getConfPaperReview().getReviewingMode()
        reviewManager = review_manager
        canAssignReferee = self._conf.getConfPaperReview().isPaperReviewManager(self._aw.getUser()) or self._conf.canModify(self._aw)

        vars["Conference"] = self._conf
        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["Contribution"] = self.__target
        vars["ConferenceChoice"] = conferenceChoice
        vars["ConferenceChoiceStr"] = conferenceChoiceStr
        vars["ContributionReviewManager"] = reviewManager
        vars["CanAssignReferee"] = canAssignReferee
        vars["CanAssignEditorOrReviewers"] = reviewManager.isReferee(self._aw.getUser()) or canAssignReferee
        vars["AvailableReviewers"] =  [r for r in  self._conf.getConference().getConfPaperReview().getReviewersList() \
                                       if r not in reviewManager.getReviewersList()]
        vars["CanEditDueDates"] = canAssignReferee
        vars["IsReferee"] = review_manager.isReferee(self._rh._getUser())
        vars["Review"] = review_manager.getLastReview()
        vars["TrackList"] = self._conf.getTrackList()

        return vars


class WPContributionReviewingJudgements( WPContributionModifBase ):

    def __init__(self, rh, contribution):
        WPContributionModifBase.__init__(self, rh, contribution)
        self._aw = rh.getAW()

    def _setActiveTab( self ):
        self._subtabReviewing.setActive()
        self._subTabJudgements.setActive()


    def _getTabContent( self, params ):
        wc = WContributionReviewingJudgements(self._target.event_new.as_legacy, self._aw)
        return wc.getHTML(self._target)

class WContributionReviewingBase(wcomponents.WTemplated):

    def _getStatusClass( self, judgement ):
        if judgement == "Accept":
            return "contributionReviewingStatusAccepted"
        elif judgement == "Reject":
            return "contributionReviewingStatusRejected"
        elif judgement == "To be corrected":
            return "contributionReviewingStatusCorrected"
        else:
            return "contributionReviewingStatusCorrected"

    def _getStatusText( self, judgement ):
        if judgement == "Accept":
            return _("ACCEPTED")
        elif judgement == "Reject":
            return _("REJECTED")
        elif judgement == "To be corrected":
            return _("To be corrected")
        else:
            return judgement

class WContributionReviewingJudgements(WContributionReviewingBase):

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw

    def getHTML(self, target):
        self.__target = target
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )

        conferenceChoice = self._conf.getConfPaperReview().getChoice()
        conferenceChoiceStr = self._conf.getConfPaperReview().getReviewingMode()
        review_manager = self._conf.getReviewManager(self.__target)
        vars["Conference"] = self._conf
        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["Contribution"] = self.__target
        vars["ConferenceChoice"] = conferenceChoice
        vars["ConferenceChoiceStr"] = conferenceChoiceStr
        vars["FinalJudge"] = review_manager.getLastReview().getRefereeJudgement().getJudgement()
        vars["Editing"] = review_manager.getLastReview().getEditorJudgement()
        vars["AdviceList"] = review_manager.getLastReview().getSubmittedReviewerJudgement()
        vars["IsReferee"] = review_manager.isReferee(self._rh._getUser())
        vars["Review"] = review_manager.getLastReview()
        vars["TrackList"] = self._conf.getTrackList()
        vars["getStatusClass"] = lambda judgement: self._getStatusClass(judgement)
        vars["getStatusText"] = lambda judgement: self._getStatusText(judgement)

        return vars



class WPJudgeEditing( WPContributionModifBase ):

    def _setActiveTab( self ):
        self._subtabReviewing.setActive()
        self._tabJudgeEditing.setActive()

    def _getTabContent( self, params ):
        wc = WJudgeEditing(self._target)
        return wc.getHTML(self._target)

class WJudgeEditing(wcomponents.WTemplated):

    def __init__(self, contrib):
        self._contrib = contrib
        self._conf = contrib.event_new.as_legacy

    def getHTML( self, target):
        return wcomponents.WTemplated.getHTML(self, {})

    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )
        review_manager = self._conf.getReviewManager(self._contrib)

        vars["Contribution"] = self._contrib
        vars['conf'] = self._conf
        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["ConferenceChoice"] = self._conf.getConfPaperReview().getChoice()
        vars["Editing"] = review_manager.getLastReview().getEditorJudgement()
        vars["Review"] = review_manager.getLastReview()

        return vars

class WPGiveAdvice( WPContributionModifBase ):

    def getJSFiles(self):
        return WPContributionModifBase.getJSFiles(self) + \
            self._includeJSPackage('Core') + \
               self._includeJSPackage('Legacy')

    def _setActiveTab( self ):
        self._subtabReviewing.setActive()
        self._tabGiveAdvice.setActive()


    def _getTabContent( self, params ):
        wc = WGiveAdvice(self._target, self._getAW())
        return wc.getHTML()

class WGiveAdvice(wcomponents.WTemplated):

    def __init__(self, contrib, aw):
        self._contrib = contrib
        self._conf = contrib.event_new.as_legacy
        self._aw = aw

    def getHTML( self):
        self.__reviewer = self._aw.getUser()
        return wcomponents.WTemplated.getHTML(self, {})

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        review_manager = self._conf.getReviewManager(self._contrib)

        vars["Conference"] = self._conf
        vars["Contribution"] = self._contrib
        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["ConferenceChoice"] = self._conf.getConfPaperReview().getChoice()
        vars["Advice"] = review_manager.getLastReview().getAdviceFrom(self.__reviewer)
        vars["Review"] = review_manager.getLastReview()

        return vars

class WPContributionReviewingHistory(WPContributionModifBase):

    def _setActiveTab( self ):
        self._subtabReviewing.setActive()
        self._subTabReviewingHistory.setActive()

    def _getTabContent( self, params ):
        wc = WContributionReviewingHistory(self._target)
        return wc.getHTML({"ShowReviewingTeam" : True})

class WContributionReviewingHistory(WContributionReviewingBase):

    def __init__(self, contribution):
        self._contribution = contribution
        self._conf = contribution.event_new.as_legacy

    def getHTML( self, params ):

        return wcomponents.WTemplated.getHTML(self, params)

    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )

        vars["ConferenceChoice"] = self._conf.getConfPaperReview().getChoice()
        vars["Versioning"] = self._conf.getReviewManager(self._contribution).getSortedVerioning()
        vars["getStatusClass"] = lambda judgement: self._getStatusClass(judgement)
        vars["getStatusText"] = lambda judgement: self._getStatusText(judgement)

        return vars
