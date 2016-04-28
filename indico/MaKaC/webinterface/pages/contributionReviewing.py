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

from flask import session

from indico.web.flask.util import url_for
from MaKaC.common.TemplateExec import render
from MaKaC.i18n import _
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase


class WPContributionModifBase(WPConferenceModifBase):
    def __init__(self, rh, contribution, **kwargs):
        WPConferenceModifBase.__init__(self, rh, contribution.event_new.as_legacy, **kwargs)
        self._contrib = self._target = contribution
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
        self._isPRM = RCPaperReviewManager.hasRights(rh)
        self._canModify = self._contrib.can_manage(session.user)

    def _getEnabledControls(self):
        return False

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": True}
        return wcomponents.WNavigationDrawer(pars, bgColor="white")

    def _createTabCtrl(self):
        review_manager = self._conf.getReviewManager(self._contrib)

        self._tabCtrl = wcomponents.TabControl()

        hasReviewingEnabled = self._conf.hasEnabledSection('paperReviewing')
        paperReviewChoice = self._conf.getConfPaperReview().getChoice()

        if hasReviewingEnabled and paperReviewChoice != 1:
            if self._canModify or self._isPRM or review_manager.isReferee(self._rh._getUser()):
                self._subtabReviewing = self._tabCtrl.newTab(
                    "reviewing", _("Paper Reviewing"), url_for('event_mgmt.contributionReviewing', self._target))
            else:
                if review_manager.isEditor(self._rh._getUser()):
                    self._subtabReviewing = self._tabCtrl.newTab(
                        "reviewing", _("Paper Reviewing"), url_for('event_mgmt.confListContribToJudge-asEditor',
                                                                   self._target))
                elif review_manager.isReviewer(self._rh._getUser()):
                    self._subtabReviewing = self._tabCtrl.newTab(
                        "reviewing", _("Paper Reviewing"), url_for('event_mgmt.confListContribToJudge-asReviewer',
                                                                   self._target))

            if self._canModify or self._isPRM or review_manager.isReferee(self._rh._getUser()):
                self._subTabAssign = self._subtabReviewing.newSubTab(
                    "assign", _("Assign Team"), url_for('event_mgmt.contributionReviewing', self._target))
                if review_manager.isReferee(self._rh._getUser()) and paperReviewChoice not in (1, 3):
                    self._subTabJudgements = self._subtabReviewing.newSubTab(
                        "referee", _("Referee Assessment"), url_for('event_mgmt.confListContribToJudge', self._target))
                else:
                    self._subTabJudgements = self._subtabReviewing.newSubTab(
                        "Assessments", _("Assessments"), url_for('event_mgmt.confListContribToJudge', self._target))

            if (paperReviewChoice == 3 or paperReviewChoice == 4) and \
                    review_manager.isEditor(self._rh._getUser()) and \
                    not review_manager.getLastReview().getRefereeJudgement().isSubmitted():
                self._tabJudgeEditing = self._subtabReviewing.newSubTab(
                    "editing", _("Assess Layout"), url_for('event_mgmt.contributionEditingJudgement', self._target))

            if (paperReviewChoice == 2 or paperReviewChoice == 4) and \
                    review_manager.isReviewer(self._rh._getUser()) and \
                    not review_manager.getLastReview().getRefereeJudgement().isSubmitted():
                self._tabGiveAdvice = self._subtabReviewing.newSubTab(
                    "advice", _("Assess Content"), url_for('event_mgmt.contributionGiveAdvice', self._target))

            if self._canModify or \
                    self._isPRM or \
                    review_manager.isReferee(self._rh._getUser()) or \
                            len(review_manager.getVersioning()) > 1 or \
                    review_manager.getLastReview().getRefereeJudgement().isSubmitted():
                self._subTabReviewingHistory = self._subtabReviewing.newSubTab(
                    "reviewing_history", _("History"), url_for('event_mgmt.contributionReviewing-reviewingHistory',
                                                               self._target))

        self._setActiveTab()
        self._setupTabCtrl()

    def _setActiveTab(self):
        pass

    def _setupTabCtrl(self):
        pass

    @property
    def sidemenu_option(self):
        return 'timetable' if self._target.timetable_entry else 'contributions'

    def _getPageContent(self, params):
        self._createTabCtrl()
        banner = ""
        if self._canModify or self._isPRM:
            if self._conf.getConfPaperReview().isRefereeContribution(self._rh._getUser(), self._contrib):
                banner = wcomponents.WListOfPapersToReview(self._target, "referee").getHTML()
            if self._conf.getConfPaperReview().isReviewerContribution(self._rh._getUser(), self._contrib):
                banner = wcomponents.WListOfPapersToReview(self._target, "reviewer").getHTML()
            if self._conf.getConfPaperReview().isEditorContribution(self._rh._getUser(), self._contrib):
                banner = wcomponents.WListOfPapersToReview(self._target, "editor").getHTML()

        body = wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))
        return banner + body

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
               '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                          for url in self._asset_env['mathjax_js'].urls()])

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._asset_env['abstracts_js'].urls()


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
