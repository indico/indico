# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.i18n import _
import MaKaC.webinterface.pages.conferences as conferences
from MaKaC.paperReviewing import ConferencePaperReview as CPR
#============================================================
#==================== Reviewing =============================
#============================================================

class WPConfModifReviewingBase(WPConferenceModifBase):
    """ Configuration of subtabs of the Reviewing tab: for each tab, a class inherits from this one
    """

    _userData = ['favorite-user-list']

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
        self._isPRM = RCPaperReviewManager.hasRights(rh)
        self._canModify = self._conf.canModify(rh.getAW())

        self._showListContribToJudge = self._conf.getConfPaperReview().isReferee(rh._getUser())

        self._showListContribToJudgeAsReviewer = self._conf.getConfPaperReview().isReviewer(rh._getUser())

        self._showListContribToJudgeAsEditor = self._conf.getConfPaperReview().isEditor(rh._getUser())

        self._showAssignContributions = self._canModify or self._isPRM or self._conf.getConfPaperReview().isReferee(rh._getUser())


    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        if self._isPRM or self._canModify:
            self._subTabPaperReviewingSetup = self._tabCtrl.newTab( "revsetup", _("Setup"),\
                urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf ) )
            self._tabPaperReviewingControl = self._tabCtrl.newTab( "revcontrol", _("Team"),\
                    urlHandlers.UHConfModifReviewingControl.getURL( self._conf ) )
            self._tabUserCompetencesReviewing = self._tabCtrl.newTab( "revcompetences", _("Competences"),\
                    urlHandlers.UHConfModifUserCompetences.getURL( self._conf ) )


        if self._showAssignContributions:
            self._tabAssignContributions = self._tabCtrl.newTab( "assignContributions", _("Assign papers"),\
                    urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf ) )

        if self._showListContribToJudge and (self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING):
            self._tabListContribToJudge = self._tabCtrl.newTab( "contributionsToJudge", _("Assess as Referee"),\
                    urlHandlers.UHConfModifListContribToJudge.getURL( self._conf ) )
        if self._showListContribToJudgeAsReviewer and (self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING):
            self._tabListContribToJudgeAsReviewer = self._tabCtrl.newTab( "contributionsToJudge", _("Assess as Content Reviewer"),\
                    urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL( self._conf ) )
        if self._showListContribToJudgeAsEditor and (self._conf.getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING):
            self._tabListContribToJudgeAsEditor = self._tabCtrl.newTab( "contributionsToJudge", _("Assess as Layout Reviewer"),\
                    urlHandlers.UHConfModifListContribToJudgeAsEditor.getURL( self._conf ) )

        self._setActiveTab()


    def _getPageContent(self, params):
        self._createTabCtrl()
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveSideMenuItem(self):
        self._reviewingMenuItem.setActive()

    def _setActiveTab(self):
        pass

#classes for paper reviewing setup tab
class WPConfModifReviewingPaperSetup(WPConfModifReviewingBase):
    """ Tab for setup of general aspects of the paper reviewing process
    """

    def __init__(self, rh, target):
        WPConfModifReviewingBase.__init__(self, rh, target)

    def _setActiveTab( self ):
        self._subTabPaperReviewingSetup.setActive()

    def _getTabContent(self, params):
        wc = WConfModifReviewingPaperSetup(self._conf)
        p = {'setTemplateURL': urlHandlers.UHSetTemplate.getURL(self._conf)}
        return wc.getHTML(p)


class WConfModifReviewingPaperSetup(wcomponents.WTemplated):
    """ Template for the previous class (WPConfModifReviewingPaperSetup)
    """

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["states"] = self._conf.getConfPaperReview().getStatuses()
        vars["reviewingQuestions"] = self._conf.getConfPaperReview().getReviewingQuestions()
        vars["criteria"] = self._conf.getConfPaperReview().getLayoutQuestions()
        return vars

    def getHTML(self, params):
        rc = WConfModificationReviewingSettings().getHTML(self._conf, params["setTemplateURL"])

        return """<br><table width="100%%" class="revtab"><tr><td>%s<br><br></td></tr></table>""" % rc


class WConfModificationReviewingSettings(wcomponents.WTemplated):
    """ Template used by the previous one (WConfModifReviewingPaperSetup)
    """

    def getHTML(self, target, setTemplateURL):
        self.__target = target
        params = {'setTemplateURL': setTemplateURL}
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )

        #choose type of reviewing
        vars["ConfReview"] = self.__target.getConfPaperReview()
        vars["choice"] = self.__target.getConfPaperReview().getChoice()
        vars["CanDelete"] = True

        #add new states
        stateAdd = []
        ht = []
        if self.__target.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING or self.__target.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING:
            stateAdd.append("""
        <td>
            Name of the new status <INPUT type=textarea name="state">
        </td>
        <td>
            <input type="submit" class="btn" value="add">
        </td>
        """)


            """displays states with checkboxes to select those to remove"""
            if len(self.__target.getConfPaperReview().getStatuses()) == 0:
                ht = "No personal states defined"
            else:
                for s in self.__target.getConfPaperReview().getStatuses():
                    ht.append("""
                    <tr>
                        <td style="border-bottom: 1px solid #5294CC;">
                            <input type="radio" name="stateSelection" value="%s">
                        </td>
                        <td align="left" style="border-bottom: 1px solid #5294CC;">%s</td></tr>
                        """%(s, s))
                ht.append("""<tr><td width="20%%">
                <input type="submit" class="btn" value="remove">
            </td>
                    </tr>""")

        ht="""<table cellspacing="0" cellpadding="5" width="50%%">%s</table>"""%"".join(ht)
        stateAdd="""%s"""%"".join(stateAdd)

        #add questions
        questionAdd = []
        qs = []
        if self.__target.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING or self.__target.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING:
            questionAdd.append("""<td>New question <INPUT type=text size="70" name="question">
            </td>
            <td>
            <input type="submit" class="btn" value="add">
            </td>""")

            """displays questions with checkboxes to select those to remove"""
            if len(self.__target.getConfPaperReview().getReviewingQuestions()) == 0:
                qs = "No question defined"
            else:
                for i in self.__target.getConfPaperReview().getReviewingQuestions():
                    qs.append("""
                    <tr>
                        <td style="border-bottom: 1px solid #5294CC;">
                            <input type="radio" name="questionSelection" value="%s">
                        </td>
                        <td align="left" style="border-bottom: 1px solid #5294CC;">%s</td>
                    </tr>"""%(i, i))
                qs.append("""<tr><td width="20%%">
                <input type="submit" class="btn" value="remove">
            </td>""")
        qs="""<table cellspacing="0" cellpadding="5" width="50%%">%s</table>"""%"".join(qs)

        questionAdd="""%s"""%"".join(questionAdd)

        #add criteria
        criteriaAdd=[]
        cs = []

        if self.__target.getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING or self.__target.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING:
            criteriaAdd.append("""<td>New criteria <INPUT type=textarea name="criteria">
        </td>
        <td>
            <input type="submit" class="btn" value="add">
        </td>""")



            """displays criteria with checkboxes to select those to remove"""
            if len(self.__target.getConfPaperReview().getLayoutQuestions()) == 0:
                cs = "No criteria defined"
            else:
                for i in self.__target.getConfPaperReview().getLayoutQuestions():
                    cs.append("""
                    <tr>
                        <td style="border-bottom: 1px solid #5294CC;">
                            <input type="radio" name="criteriaSelection" value="%s">
                        </td>
                        <td align="left" style="border-bottom: 1px solid #5294CC;">%s</td>
                    </tr>"""%(i, i))
                cs.append("""<td width="20%%">
                <input type="submit" class="btn" value="remove">
            </td>""")
        cs="""<table cellspacing="0" cellpadding="5" width="50%%">%s</table>"""%"".join(cs)

        criteriaAdd="""%s"""%"".join(criteriaAdd)

        #return vars
        vars["criteriaAdd"] = criteriaAdd
        vars["questionAdd"] = questionAdd
        vars["stateAdd"] = stateAdd
        vars["stateTable"] = ht
        vars["questionTable"] = qs
        vars["criteriaTable"] = cs
        vars["reviewingModesDict"] = {}
        for i in self.__target.getConfPaperReview().reviewingModes:
            vars["reviewingModesDict"][i] = i
        return vars


class WContributionReviewingTemplatesList(wcomponents.WTemplated):
    """ Component that shows list of paper reviewing templates
    """

    def __init__(self, conference):
        self._conf = conference

    def getHTML(self, params):
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["ConfReview"] = self._conf.getConfPaperReview()
        return vars

#classes for control tab
class WPConfModifReviewingControl(WPConfModifReviewingBase):
    """ Tab for reviewing's access control (designing referees, etc.)
    """
    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, target):
        WPConfModifReviewingBase.__init__(self, rh, target)

    def _setActiveTab( self ):
        self._tabPaperReviewingControl.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifReviewingControl( self._conf )
        return wc.getHTML(params)


class WConfModifReviewingControl(wcomponents.WTemplated):
    """ Template for the previous class. Uses the 2 next classes as templates
    """

    def __init__( self, conference):
        self._conf = conference

    def getHTML( self, params ):

        rc=""
        rcPRM=""

        if self._conf.getConfPaperReview().getChoice() == CPR.NO_REVIEWING:
            message = _("Type of reviewing has not been chosen yet. You can choose it from Paper Reviewing ")
            setupText = _("Setup.")
            return """<table align="left"><tr><td style="padding-left: 25px; padding-top:10px; color:gray;">
                    %s
                    <a href="%s">%s</a></td></tr></table>"""% (message, urlHandlers.UHConfModifReviewingPaperSetup.getURL(self._conf), setupText)
        else:
            rcPRM = WConfModificationReviewingFramePRM().getHTML(self._conf)

            rc = WConfModificationReviewingFrame().getHTML( self._conf)

            return """<table width="100%%" class="Revtab"><tr><td>%s</td></tr><tr><td>%s</td></tr></table>"""%(rcPRM, rc)


class WConfModificationReviewingFramePRM(wcomponents.WTemplated):
    """Template used by previous class. For the list of review managers of the conference
    """

    def getHTML( self, target):
        self.__target = target
        return  wcomponents.WTemplated.getHTML( self )

    def getVars( self ):

        vars = wcomponents.WTemplated.getVars( self )

        vars["Conference"] = self.__target.getId()
        vars["ConfReview"] = self.__target.getConfPaperReview()
        return vars


class WConfModificationReviewingFrame(wcomponents.WTemplated):
    """ Template used by WConfModifReviewingControl,
        for the list of referees, editors and reviewers of the conference.
    """

    def getHTML( self, target):
        self.__target = target
        return  wcomponents.WTemplated.getHTML( self )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["Conference"] = self.__target.getId()
        vars["ConfReview"] = self.__target.getConfPaperReview()
        return vars

#classes for contributions to judge list tab
class WPConfListContribToJudge(WPConfModifReviewingBase):
    """ Tab to see the logged user's list of contributions
        to judge (as a referee, editor, or reviewer)
    """

    def __init__(self, rh, conference):
        self._user = rh._getUser()
        WPConfModifReviewingBase.__init__(self, rh, conference)

    def _setActiveTab( self ):
        self._tabListContribToJudge.setActive()

    def _getTabContent( self, params ):
        wc = WConfListContribToJudge(self._conf, self._user)
        return wc.getHTML()

class WConfListContribToJudge(wcomponents.WTemplated):
    """ Template used to show list of contributions to judge / edit / give advice on
    """

    def __init__(self, conf, user):
        self._conf = conf
        self._user = user

    def getHTML(self):
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["User"] = self._user

        return vars

class WPConfListContribToJudgeAsReviewer(WPConfModifReviewingBase):
    """ Tab to see the logged user's list of contributions
        to judge (as reviewer)
    """

    def __init__(self, rh, conference):
        self._user = rh._getUser()
        WPConfModifReviewingBase.__init__(self, rh, conference)

    def _setActiveTab( self ):
        self._tabListContribToJudgeAsReviewer.setActive()

    def _getTabContent( self, params ):
        wc = WConfListContribToJudgeAsReviewer(self._conf, self._user)
        return wc.getHTML()

class WConfListContribToJudgeAsReviewer(wcomponents.WTemplated):
    """ Template used to show list of contributions to give advice on
    """

    def __init__(self, conf, user):
        self._conf = conf
        self._user = user

    def getHTML(self):
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["User"] = self._user

        return vars

class WPConfListContribToJudgeAsEditor(WPConfModifReviewingBase):
    """ Tab to see the logged user's list of contributions
        to judge (as editor)
    """

    def __init__(self, rh, conference):
        self._user = rh._getUser()
        WPConfModifReviewingBase.__init__(self, rh, conference)

    def _setActiveTab( self ):
        self._tabListContribToJudgeAsEditor.setActive()

    def _getTabContent( self, params ):
        wc = WConfListContribToJudgeAsEditor(self._conf, self._user)
        return wc.getHTML()

class WConfListContribToJudgeAsEditor(wcomponents.WTemplated):
    """ Template used to show list of contributions to edit
    """

    def __init__(self, conf, user):
        self._conf = conf
        self._user = user

    def getHTML(self):
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["User"] = self._user

        return vars

#classes for assign contributions tab
class WPConfReviewingAssignContributions(WPConfModifReviewingBase):
    """ Tab to see the logged user's list of contributions
        to judge (as a referee, editor, or reviewer)
    """

    def __init__(self, rh, conference):
        self._aw = rh.getAW()
        WPConfModifReviewingBase.__init__(self, rh, conference)

    def _setActiveTab( self ):
        self._tabAssignContributions.setActive()

    def _getTabContent( self, params ):
        wc = WConfReviewingAssignContributions(self._conf, self._aw)
        return wc.getHTML()

class WConfReviewingAssignContributions(wcomponents.WTemplated):
    """ Template used to show list of contributions to judge / edit / give advice on
    """

    def __init__(self, conf, aw):
        self._conf = conf
        self._aw = aw

    def getHTML(self):
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["Conference"] = self._conf
        vars["ConfReview"] = self._conf.getConfPaperReview()
        vars["IsOnlyReferee"] = self._conf.getConfPaperReview().isReferee(self._aw.getUser()) and not self._conf.canModify(self._aw) and not self._conf.getConfPaperReview().isPaperReviewManager(self._aw.getUser())

        return vars

#classes for user competences tab
class WPConfModifUserCompetences(WPConfModifReviewingBase):
    """ Tab to see the user competences
    """

    def __init__(self, rh, conference):
        WPConfModifReviewingBase.__init__(self, rh, conference)

    def _setActiveTab( self ):
        self._tabUserCompetencesReviewing.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifUserCompetences(self._conf)
        return wc.getHTML()

class WConfModifUserCompetences(wcomponents.WTemplated):
    """ Template used to show list of contributions to judge / edit / give advice on
    """

    def __init__(self, conf):
        self._conf = conf

    def getHTML(self):
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["Conference"] = self._conf
        vars["ConfReview"] = self._conf.getConfPaperReview()

        return vars
