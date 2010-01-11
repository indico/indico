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
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.webinterface.pages.conferences import WPConferenceModifAbstractBase
from MaKaC.i18n import _
import MaKaC.webinterface.pages.conferences as conferences
#============================================================
#==================== Reviewing =============================
#============================================================

class WPConfModifReviewingBase(WPConferenceModifBase):
    """ Configuration of subtabs of the Reviewing tab: for each tab, a class inherits from this one
    """

    _userData = ['favorite-user-list']

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCAbstractManager
        self._isPRM = RCPaperReviewManager.hasRights(rh)
        self._isAM = RCAbstractManager.hasRights(rh)
        self._canModify = self._conf.canModify(rh.getAW())
                                           
        self._showListContribToJudge = self._conf.getConfReview().isReferee(rh._getUser())
    
        self._showListContribToJudgeAsReviewer = self._conf.getConfReview().isReviewer(rh._getUser())
                                       
        self._showListContribToJudgeAsEditor = self._conf.getConfReview().isEditor(rh._getUser())
        
        self._showAssignContributions = self._canModify or self._isPRM or self._conf.getConfReview().isReferee(rh._getUser())

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        
        if self._isPRM or self._canModify:
            self._subtabPaperReviewing = self._tabCtrl.newTab( "paperrev", "Paper Reviewing", \
                urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf ) )
        elif self._showAssignContributions:
            self._subtabPaperReviewing = self._tabCtrl.newTab( "paperrev", "Paper Reviewing", \
                urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf ) )
        elif self._showListContribToJudgeAsEditor:
            self._subtabPaperReviewing = self._tabCtrl.newTab( "paperrev", "Paper Reviewing", \
                urlHandlers.UHConfModifListContribToJudgeAsEditor.getURL( self._conf ) )
        else:
            self._subtabPaperReviewing = self._tabCtrl.newTab( "paperrev", "Paper Reviewing", \
                urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL( self._conf ) )
        
        if self._isAM or self._canModify:
            self._subtabAbstractsReviewing = self._tabCtrl.newTab( "abstractsrev", "Abstracts Reviewing", \
                urlHandlers.UHConfModifReviewingAbstractSetup.getURL( target = self._conf ) )
        
        if self._isPRM or self._canModify:
            self._subTabPaperReviewingSetup = self._subtabPaperReviewing.newSubTab( "revsetup", "Setup",\
                urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf ) )
            self._tabPaperReviewingControl = self._subtabPaperReviewing.newSubTab( "revcontrol", "Team",\
                    urlHandlers.UHConfModifReviewingControl.getURL( self._conf ) )
            self._tabUserCompetencesReviewing = self._subtabPaperReviewing.newSubTab( "revcompetences", "Competences",\
                    urlHandlers.UHConfModifUserCompetences.getURL( self._conf ) )
            
        if self._isAM or self._canModify:
            self._tabAbstractReviewingSetup = self._subtabAbstractsReviewing.newSubTab( "revsetup", "Setup",\
                    urlHandlers.UHConfModifReviewingAbstractSetup.getURL(target = self._conf) )
            self._tabAbstractNotifTpl = self._subtabAbstractsReviewing.newSubTab( "notiftpl", "Notification templates",\
                    urlHandlers.UHAbstractReviewingNotifTpl.getURL(target = self._conf) )
            self._tabAbstractsReviewingControl = self._subtabAbstractsReviewing.newSubTab( "abscontrol", "Team",\
                    urlHandlers.UHConfModifReviewingAbstractsControl.getURL( self._conf ) ) 
            self._tabUserCompetencesAbstracts = self._subtabAbstractsReviewing.newSubTab( "abscompetences", "Competences",\
                    urlHandlers.UHConfModifUserCompetencesAbstracts.getURL( self._conf ) )
            self._tabAbstractList = self._subtabAbstractsReviewing.newSubTab( "abstractList", "List of Abstracts",\
                    urlHandlers.UHConfAbstractList.getURL( self._conf ) )
            
        
        if self._showAssignContributions:
            self._tabAssignContributions = self._subtabPaperReviewing.newSubTab( "assignContributions", "Assign Contributions",\
                    urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf ) )   
        
        if self._showListContribToJudge:
            self._tabListContribToJudge = self._subtabPaperReviewing.newSubTab( "contributionsToJudge", "Judge as Referee",\
                    urlHandlers.UHConfModifListContribToJudge.getURL( self._conf ) )
        if self._showListContribToJudgeAsReviewer:
            self._tabListContribToJudgeAsReviewer = self._subtabPaperReviewing.newSubTab( "contributionsToJudge", "Judge as Content Reviewer",\
                    urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL( self._conf ) )
        if self._showListContribToJudgeAsEditor:
            self._tabListContribToJudgeAsEditor = self._subtabPaperReviewing.newSubTab( "contributionsToJudge", "Judge as Layout Reviewer",\
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
   
    def _getTabContent( self, params ):
        wc = WConfModifReviewingPaperSetup( self._conf)
        p = { # probably these values are not needed (except setTemplateURL) any more since now all these things are done by services
             "choiceURL": urlHandlers.UHChooseReviewing.getURL(self._conf), \
             "addStateURL": urlHandlers.UHAddState.getURL(self._conf), \
             "removeStateURL": urlHandlers.UHRemoveState.getURL(self._conf), \
             "addQuestionURL": urlHandlers.UHAddQuestion.getURL(self._conf), \
             "removeQuestionURL": urlHandlers.UHRemoveQuestion.getURL(self._conf), \
             "setTemplateURL": urlHandlers.UHSetTemplate.getURL(self._conf), \
             "addCriteriaURL": urlHandlers.UHAddCriteria.getURL(self._conf), \
             "removeCriteriaURL": urlHandlers.UHRemoveCriteria.getURL(self._conf), \
             }
        return wc.getHTML( p )

class WConfModifReviewingPaperSetup(wcomponents.WTemplated):
    """ Template for the previous class (WPConfModifReviewingPaperSetup)
    """

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["states"] = self._conf.getConferenceReview().getStates()
        vars["reviewingQuestions"] = self._conf.getConferenceReview().getReviewingQuestions()
        vars["criteria"] = self._conf.getConferenceReview().getLayoutCriteria()
        return vars

    def getHTML(self, params):
        rc= WConfModificationReviewingSettings().getHTML( self._conf,\
                                                    params["choiceURL"], \
                                                    params["addStateURL"], \
                                                    params["removeStateURL"], \
                                                    params["addQuestionURL"], \
                                                    params["removeQuestionURL"], \
                                                    params["setTemplateURL"], \
                                                    params["addCriteriaURL"], \
                                                    params["removeCriteriaURL"])

        return """<br><table width="100%%" class="revtab"><tr><td>%s<br><br></td></tr></table>"""%(rc)


class WConfModificationReviewingSettings(wcomponents.WTemplated):
    """ Template used by the previous one (WConfModifReviewingPaperSetup)
    """

    def getHTML( self, target, choiceURL, addStateURL, removeStateURL, addQuestionURL, removeQuestionURL, setTemplateURL, addCriteriaURL, removeCriteriaURL ):
        self.__target = target
        params = { "choiceURL": choiceURL, \
                   "addStateURL": addStateURL, \
                   "removeStateURL": removeStateURL, \
                   "addQuestionURL": addQuestionURL, \
                   "removeQuestionURL": removeQuestionURL, \
                   "setTemplateURL": setTemplateURL, \
                   "addCriteriaURL": addCriteriaURL, \
                   "removeCriteriaURL": removeCriteriaURL}

        return  wcomponents.WTemplated.getHTML( self, params )

    def getVars( self):
        vars = wcomponents.WTemplated.getVars( self )

        #choose type of reviewing
        vars["ConfReview"] = self.__target.getConfReview()
        vars["choice"] = self.__target.getConfReview().getChoice()
        vars["CanDelete"] = True

        #add new states
        stateAdd = []
        ht = []
        if self.__target.getConfReview().getChoice() == 2 or self.__target.getConfReview().getChoice() == 4 :
            stateAdd.append("""
        <td>
            Name of the new status <INPUT type=textarea name="state">
        </td>
        <td>
            <input type="submit" class="btn" value="add">
        </td>
        """)


            """displays states with checkboxes to select those to remove"""
            if len(self.__target.getConfReview().getStates()) == 0:
                ht = "No personal states defined"
            else:
                for s in self.__target.getConfReview().getStates():
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
        if self.__target.getConfReview().getChoice() == 2 or self.__target.getConfReview().getChoice() == 4:
            questionAdd.append("""<td>New question <INPUT type=text size="70" name="question">
            </td>
            <td>
            <input type="submit" class="btn" value="add">
            </td>""")

            """displays questions with checkboxes to select those to remove"""
            if len(self.__target.getConfReview().getReviewingQuestions()) == 0:
                qs = "No question defined"
            else:
                for i in self.__target.getConfReview().getReviewingQuestions():
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

        if self.__target.getConfReview().getChoice() == 3 or self.__target.getConfReview().getChoice() == 4:
            criteriaAdd.append("""<td>New criteria <INPUT type=textarea name="criteria">
        </td>
        <td>
            <input type="submit" class="btn" value="add">
        </td>""")



            """displays criteria with checkboxes to select those to remove"""
            if len(self.__target.getConfReview().getLayoutCriteria()) == 0:
                cs = "No criteria defined"
            else:
                for i in self.__target.getConfReview().getLayoutCriteria():
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
        vars["ConfReview"] = self._conf.getConfReview()
        return vars

#classes for abstract reviewing setup tab
class WPConfModifAbstractReviewing(WPConfModifReviewingBase):
    """ Tab for setup of general aspects of the abstract reviewing process
    """

    def __init__(self, rh, target):
        WPConfModifReviewingBase.__init__(self, rh, target)

    def _setActiveTab( self ):
        self._subtabAbstractsReviewing.setActive()
        self._tabAbstractReviewingSetup.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifAbstractReviewingSettings(self._conf)
        params = {}
        return wc.getHTML( params )    

class WPConfAbstractList( WPConfModifReviewingBase ):
    
    def __init__(self, rh, conf, msg):
        self._msg = msg
        WPConfModifReviewingBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        order = params.get("order","down")
        websession = self._rh._getSession()
        wc = conferences.WAbstracts( self._conf, params.get("filterCrit", None ), \
                            params.get("sortingCrit", None),order, params.get("fields", None), params.get("menuStatus", None), websession )
        p = {"authSearch":params.get("authSearch","")}
        return wc.getHTML( p )
    
    def _setActiveTab(self):
        self._subtabAbstractsReviewing.setActive()
        self._tabAbstractReviewingSetup.setActive()

class WConfModifAbstractReviewingSettings(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["ConfReview"] = self._conf.getConfReview()
        return vars   

#classes for control tab
class WPConfModifReviewingControl(WPConfModifReviewingBase):
    """ Tab for reviewing's access control (designing referees, etc.)
    """

    def __init__(self, rh, target):
        WPConfModifReviewingBase.__init__(self, rh, target)

    def _setActiveTab( self ):
        self._tabPaperReviewingControl.setActive()
   
    def _getTabContent( self, params ):
        wc = WConfModifReviewingControl( self._conf )
        p = {
            "addPaperReviewManagerURL": urlHandlers.UHConfSelectPaperReviewManager.getURL(), \
            "removePaperReviewManagerURL": urlHandlers.UHConfRemovePaperReviewManager.getURL(), \
            "addEditorURL": urlHandlers.UHConfSelectEditor.getURL(), \
            "removeEditorURL": urlHandlers.UHConfRemoveEditor.getURL(), \
            "addReviewerURL": urlHandlers.UHConfSelectReviewer.getURL(), \
            "removeReviewerURL": urlHandlers.UHConfRemoveReviewer.getURL(), \
            "addRefereeURL": urlHandlers.UHConfSelectReferee.getURL(), \
            "removeRefereeURL": urlHandlers.UHConfRemoveReferee.getURL(), \
            }
        return wc.getHTML( p )
 
#class for setting up abstract notification templates
class WPConfModifAbstractsReviewingNotifTpl( WPConfModifReviewingBase ):
    
    def _setActiveTab( self ):
        self._tabAbstractNotifTpl.setActive() 
        self._subtabAbstractsReviewing.setActive()
    
    def _getTabContent( self, params ):
        wc = conferences.WAbstractsReviewingNotifTpl( self._conf )
        return wc.getHTML()
 
class WPModCFANotifTplNew(WPConfModifReviewingBase):
    
    def _setActiveTab( self ):
        self._tabAbstractNotifTpl.setActive() 
        self._subtabAbstractsReviewing.setActive()
    
    def _getTabContent(self,params):
        wc = conferences.WConfModCFANotifTplNew(self._conf)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)      

class WPConfReviewingAbstractList( WPConfModifReviewingBase):
    
    def __init__(self, rh, conf, msg):
        self._msg = msg
        WPConfModifReviewingBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        order = params.get("order","down")
        websession = self._rh._getSession()
        wc = conferences.WAbstracts( self._conf, params.get("filterCrit", None ), \
                            params.get("sortingCrit", None),order, params.get("fields", None), params.get("menuStatus", None), websession )
        p = {"authSearch":params.get("authSearch","")}
        return wc.getHTML( p )
    
    def _setActiveTab(self):
        self._subtabAbstractsReviewing.setActive()
        self._tabAbstractList.setActive()                       
        
            
class WConfModifReviewingControl(wcomponents.WTemplated):
    """ Template for the previous class. Uses the 2 next classes as templates
    """

    def __init__( self, conference):
        self._conf = conference

    def getHTML( self, params ):

        rc=""
        rcPRM=""

        if self._conf.getConfReview().getChoice() != 1 and self._conf.getConfReview().getChoice() == 0:
            return """<table align="center"><tr><td>Type of reviewing has not been chosen yet</td></tr></table>"""
        else:
            rcPRM = WConfModificationReviewingFramePRM().getHTML(self._conf, \
                                                params["addPaperReviewManagerURL"], \
                                                params["removePaperReviewManagerURL"])

            rc = WConfModificationReviewingFrame().getHTML( self._conf,\
                                                params["addRefereeURL"], \
                                                params["removeRefereeURL"], \
                                                params["addEditorURL"], \
                                                params["removeEditorURL"], \
                                                params["addReviewerURL"], \
                                                params["removeReviewerURL"])
            
            return """<table width="100%%" class="Revtab"><tr><td>%s%s</td></tr></table>"""%(rcPRM, rc)


class WConfModificationReviewingFramePRM(wcomponents.WTemplated):
    """Template used by previous class. For the list of review managers of the conference
    """

    def getHTML( self, target, addPaperReviewManagerURL, removePaperReviewManagerURL):
        self.__target = target
        params = { "addPaperReviewManagerURL": addPaperReviewManagerURL, \
                   "removePaperReviewManagerURL": removePaperReviewManagerURL}
        return  wcomponents.WTemplated.getHTML( self, params )

    def getVars( self ):
        
        vars = wcomponents.WTemplated.getVars( self )

        prmTable = []
        prmTable.append(_("""<td nowrap class="titleCellTD"><span class="titleCellFormat"><br> _("Managers of Paper Reviewing Module")<br> <br><font size="-2">_("responsibilities:") _("Setup, Assign")<br> _(" contributions to Referees"),<br>_(" Define team competences")</font></span></td>
        """))
        #prmTable.append(wcomponents.WPrincipalTable().getHTML( self.__target.getConfReview().getPaperReviewManagersList(),
        #                                                      self.__target, vars["addPaperReviewManagerURL"], vars["removePaperReviewManagerURL"], selectable=False))
        #prmTable.append("""</td>""")
        prmTable="""%s"""%"".join(prmTable)
        vars["Conference"] = self.__target.getId()
        vars["ConfReview"] = self.__target.getConfReview()
        vars["paperReviewManagerTable"] = prmTable
        return vars


class WConfModificationReviewingFrame(wcomponents.WTemplated):
    """ Template used by WConfModifReviewingControl,
        for the list of referees, editors and reviewers of the conference.
    """

    def getHTML( self, target, addRefereeURL, removeRefereeURL, addEditorURL, removeEditorURL, addReviewerURL, removeReviewerURL):
        self.__target = target
        params = { "addRefereeURL": addRefereeURL, \
                   "removeRefereeURL": removeRefereeURL, \
                   "addEditorURL": addEditorURL, \
                   "removeEditorURL": removeEditorURL, \
                   "addReviewerURL": addReviewerURL, \
                   "removeReviewerURL": removeReviewerURL}
        return  wcomponents.WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        editor=[]
        reviewer=[]
        refereeTable=[]

        if self.__target.getConfReview().getChoice() == 2 or self.__target.getConfReview().getChoice() == 1:
            pass
        else:
            editor.append(_("""<td nowrap class="titleCellTD"><span class="titleCellFormat">_("Layout Reviewers")<br><br><font size="-2">_("responsibility: judge")<br> _("form verification")<br>_("of contributions")</font></span></td>
            """))
            #editor.append(wcomponents.WPrincipalTable().getHTML( self.__target.getConfReview().getEditorsList(),
            #                                                     self.__target, vars["addEditorURL"], vars["removeEditorURL"], selectable=False))
            #editor.append("""</td>""")
        editor="""%s"""%"".join(editor)

        if self.__target.getConfReview().getChoice() == 3 or self.__target.getConfReview().getChoice() == 1:
            pass
        else:
            reviewer.append(_("""<td nowrap class="titleCellTD"><span class="titleCellFormat">_("Content Reviewers")<br><br><font size="-2">_("responsibility: judge")<br> _("content verification")<br>_("of contributions")</font></span></td>
            """))
            #reviewer.append(wcomponents.WPrincipalTable().getHTML( self.__target.getConfReview().getReviewersList(),
            #                                                       self.__target, vars["addReviewerURL"], vars["removeReviewerURL"], selectable=False))
            #reviewer.append("""</td>""")
        
            refereeTable.append(_("""<td width="80%%" nowrap class="titleCellTD"><span class="titleCellFormat">_("Referees")<br><br><font size="-2">_("responsiblities: Assign,")<br> _("contributions to Reviewers,")<br> _("Give final judgement")</font></span></td>
            """))
            #refereeTable.append(wcomponents.WPrincipalTable().getHTML( self.__target.getConfReview().getRefereesList(),
            #                                                          self.__target, vars["addRefereeURL"], vars["removeRefereeURL"], selectable=False))
            #refereeTable.append("""</td>""")
            
        reviewer="""%s"""%"".join(reviewer)
        refereeTable="""%s"""%"".join(refereeTable)

        vars["Conference"] = self.__target.getId()
        vars["ConfReview"] = self.__target.getConfReview()
        vars["editorTable"] = editor
        vars["reviewerTable"] = reviewer
        vars["refereeTable"] = refereeTable

class WConfModifAbstractsReviewingControl(wcomponents.WTemplated):
    """ Template for the previous class. Uses the next class as templates
    """
    
    def __init__( self, conference):
        self._conf = conference

    def getHTML( self, params ):
        
        rcAbstract=""
        rcAbstract = WConfModificationAbstractReviewingFrame().getHTML( self._conf,\
                                                params["addAbstractManagerURL"], \
                                                params["removeAbstractManagerURL"], \
                                                params["addAbstractReviewerURL"], \
                                                params["removeAbstractReviewerURL"])
        
        return """<table width="100%%" class="Revtab"><tr><td>%s</td></tr></table>"""%(rcAbstract)


class WConfModificationAbstractReviewingFrame(wcomponents.WTemplated):
    """ Template used by WConfModifReviewingControl,
        for the list of abstract managers and abstract reviewers
    """

    def getHTML( self, target, addAbstractManagerURL, removeAbstractManagerURL, addAbstractReviewerURL, removeAbstractReviewerURL):
        self.__target = target
        params = { "addAbstractManagerURL": addAbstractManagerURL,\
                   "removeAbstractManagerURL": removeAbstractManagerURL,\
                   "addAbstractReviewerURL": addAbstractReviewerURL,\
                   "removeAbstractReviewerURL": removeAbstractReviewerURL
                   }
        return  wcomponents.WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractManagerTable"] = wcomponents.WPrincipalTable().getHTML( self.__target.getConfReview().getAbstractManagersList(),
                                                                              self.__target, vars["addAbstractManagerURL"],
                                                                              vars["removeAbstractManagerURL"], selectable=False)
        vars["abstractReviewerTable"] = wcomponents.WPrincipalTable().getHTML( self.__target.getConfReview().getAbstractReviewersList(),
                                                                               self.__target, vars["addAbstractReviewerURL"],
                                                                               vars["removeAbstractReviewerURL"], selectable=False)
        return vars

class WPConfSelectPaperReviewManager( WPConfModifReviewingBase ):
    """ Page to select a PRM
    """

    def _createTabCtrl(self):
        WPConfModifReviewingBase._createTabCtrl(self)
        self._tabPaperReviewingControl.setActive()
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectPaperReviewManager.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddPaperReviewManager.getURL()
        return wc.getHTML( params )

class WPConfSelectAbstractManager( WPConfModifReviewingBase ):
    """ Page to select a PRM
    """

    def _createTabCtrl(self):
        WPConfModifReviewingBase._createTabCtrl(self)
        self._subtabAbstractsReviewing.setActive()
        self._tabAbstractsReviewingControl.setActive()
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectAbstractManager.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddAbstractManager.getURL()
        return wc.getHTML( params )

class WPConfSelectEditor( WPConfModifReviewingBase ):
    """ Page to select an editor
    """

    def _createTabCtrl(self):
        WPConfModifReviewingBase._createTabCtrl(self)
        self._tabPaperReviewingControl.setActive()
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectEditor.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddEditor.getURL()
        return wc.getHTML( params )

class WPConfSelectReviewer( WPConfModifReviewingBase ):
    """ Page to select a reviewer
    """

    def _createTabCtrl(self):
        WPConfModifReviewingBase._createTabCtrl(self)
        self._tabPaperReviewingControl.setActive()
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectReviewer.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddReviewer.getURL()
        return wc.getHTML( params )

class WPConfSelectReferee( WPConfModifReviewingBase ):
    """ Page to select a referee
    """

    def _createTabCtrl(self):
        WPConfModifReviewingBase._createTabCtrl(self)
        self._tabPaperReviewingControl.setActive()
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectReferee.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddReferee.getURL()
        return wc.getHTML( params )

class WPConfSelectAbstractReviewer( WPConfModifReviewingBase ):
    """ Page to select a PRM
    """

    def _createTabCtrl(self):
        WPConfModifReviewingBase._createTabCtrl(self)
        self._subtabAbstractsReviewing.setActive()
        self._tabAbstractsReviewingControl.setActive()
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectAbstractReviewer.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddAbstractReviewer.getURL()
        return wc.getHTML( params )

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

        vars["ConfReview"] = self._conf.getConfReview()
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
        
        vars["ConfReview"] = self._conf.getConfReview()
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
        
        vars["ConfReview"] = self._conf.getConfReview()
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
        vars["ConfReview"] = self._conf.getConfReview()
        vars["IsOnlyReferee"] = self._conf.getConfReview().isReferee(self._aw.getUser()) and not self._conf.canModify(self._aw) and not self._conf.getConfReview().isPaperReviewManager(self._aw.getUser())
        
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
        vars["ConfReview"] = self._conf.getConfReview()
        
        return vars
    
class WPConfModifUserCompetencesAbstracts(WPConfModifReviewingBase):
    """ Tab to see the user competences
    """
    
    def __init__(self, rh, conference):
        WPConfModifReviewingBase.__init__(self, rh, conference)

    def _setActiveTab( self ):
        self._tabUserCompetencesAbstracts.setActive()
        self._subtabAbstractsReviewing.setActive()
        
    def _getTabContent( self, params ):
        wc = WConfModifUserCompetencesAbstracts(self._conf)    
        return wc.getHTML()
    
class WConfModifUserCompetencesAbstracts(wcomponents.WTemplated):
    """ Template used to show list of contributions to judge / edit / give advice on
    """
    
    def __init__(self, conf):
        self._conf = conf

    def getHTML(self):
        return wcomponents.WTemplated.getHTML(self)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["Conference"] = self._conf
        vars["ConfReview"] = self._conf.getConfReview()
        
        return vars