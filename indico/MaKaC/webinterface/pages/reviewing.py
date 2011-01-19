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
from xml.sax.saxutils import quoteattr
from MaKaC.common import Config
from MaKaC import review
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
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
        #self._isAM = RCAbstractManager.hasRights(rh)
        self._canModify = self._conf.canModify(rh.getAW())

        self._showListContribToJudge = self._conf.getConfPaperReview().isReferee(rh._getUser())

        self._showListContribToJudgeAsReviewer = self._conf.getConfPaperReview().isReviewer(rh._getUser())

        self._showListContribToJudgeAsEditor = self._conf.getConfPaperReview().isEditor(rh._getUser())

        self._showAssignContributions = self._canModify or self._isPRM or self._conf.getConfPaperReview().isReferee(rh._getUser())



    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        #if self._isAM or self._canModify:
        if self._canModify:
            self._subtabAbstractsReviewing = self._tabCtrl.newTab( "abstractsrev", "Abstracts Reviewing", \
                urlHandlers.UHConfModifReviewingAbstractSetup.getURL( target = self._conf ) )

        #if self._isAM or self._canModify:
        if self._canModify:
            self._tabAbstractReviewingSetup = self._subtabAbstractsReviewing.newSubTab( "revsetup", "Setup",\
                    urlHandlers.UHConfModifReviewingAbstractSetup.getURL(target = self._conf) )
            self._tabAbstractNotifTpl = self._subtabAbstractsReviewing.newSubTab( "notiftpl", "Notification templates",\
                    urlHandlers.UHAbstractReviewingNotifTpl.getURL(target = self._conf) )
            # The following tabs are not used yet
            #self._tabAbstractsReviewingControl = self._subtabAbstractsReviewing.newSubTab( "abscontrol", "Team",\
            #        urlHandlers.UHConfModifReviewingAbstractsControl.getURL( self._conf ) )
            #self._tabUserCompetencesAbstracts = self._subtabAbstractsReviewing.newSubTab( "abscompetences", "Competences",\
            #        urlHandlers.UHConfModifUserCompetencesAbstracts.getURL( self._conf ) )
            self._tabAbstractList = self._subtabAbstractsReviewing.newSubTab( "abstractList", "List of Abstracts",\
                    urlHandlers.UHConfAbstractList.getURL( self._conf ) )

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

        if self._isPRM or self._canModify:
            self._subTabPaperReviewingSetup = self._subtabPaperReviewing.newSubTab( "revsetup", "Setup",\
                urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf ) )
            self._tabPaperReviewingControl = self._subtabPaperReviewing.newSubTab( "revcontrol", "Team",\
                    urlHandlers.UHConfModifReviewingControl.getURL( self._conf ) )
            self._tabUserCompetencesReviewing = self._subtabPaperReviewing.newSubTab( "revcompetences", "Competences",\
                    urlHandlers.UHConfModifUserCompetences.getURL( self._conf ) )


        if self._showAssignContributions:
            self._tabAssignContributions = self._subtabPaperReviewing.newSubTab( "assignContributions", "Assign Contributions",\
                    urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf ) )

        if self._showListContribToJudge and (self._conf.getConfPaperReview().getChoice()==2 or self._conf.getConfPaperReview().getChoice()==4):
            self._tabListContribToJudge = self._subtabPaperReviewing.newSubTab( "contributionsToJudge", "Judge as Referee",\
                    urlHandlers.UHConfModifListContribToJudge.getURL( self._conf ) )
        if self._showListContribToJudgeAsReviewer and (self._conf.getConfPaperReview().getChoice()==2 or self._conf.getConfPaperReview().getChoice()==4):
            self._tabListContribToJudgeAsReviewer = self._subtabPaperReviewing.newSubTab( "contributionsToJudge", "Judge as Content Reviewer",\
                    urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL( self._conf ) )
        if self._showListContribToJudgeAsEditor and (self._conf.getConfPaperReview().getChoice()==3 or self._conf.getConfPaperReview().getChoice()==4):
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
        self._subtabPaperReviewing.setActive()
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
        vars["states"] = self._conf.getConfPaperReview().getStates()
        vars["reviewingQuestions"] = self._conf.getConfPaperReview().getReviewingQuestions()
        vars["criteria"] = self._conf.getConfPaperReview().getLayoutCriteria()
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
        vars["ConfReview"] = self.__target.getConfPaperReview()
        vars["choice"] = self.__target.getConfPaperReview().getChoice()
        vars["CanDelete"] = True

        #add new states
        stateAdd = []
        ht = []
        if self.__target.getConfPaperReview().getChoice() == 2 or self.__target.getConfPaperReview().getChoice() == 4 :
            stateAdd.append("""
        <td>
            Name of the new status <INPUT type=textarea name="state">
        </td>
        <td>
            <input type="submit" class="btn" value="add">
        </td>
        """)


            """displays states with checkboxes to select those to remove"""
            if len(self.__target.getConfPaperReview().getStates()) == 0:
                ht = "No personal states defined"
            else:
                for s in self.__target.getConfPaperReview().getStates():
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
        if self.__target.getConfPaperReview().getChoice() == 2 or self.__target.getConfPaperReview().getChoice() == 4:
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

        if self.__target.getConfPaperReview().getChoice() == 3 or self.__target.getConfPaperReview().getChoice() == 4:
            criteriaAdd.append("""<td>New criteria <INPUT type=textarea name="criteria">
        </td>
        <td>
            <input type="submit" class="btn" value="add">
        </td>""")



            """displays criteria with checkboxes to select those to remove"""
            if len(self.__target.getConfPaperReview().getLayoutCriteria()) == 0:
                cs = "No criteria defined"
            else:
                for i in self.__target.getConfPaperReview().getLayoutCriteria():
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
        vars["ConfReview"] = self._conf.getConfPaperReview()
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
        vars["abstractReview"] = self._conf.getConfAbstractReview()
        #vars["reviewingQuestions"] = self._conf.getConferenceReview().getAbstractReviewingQuestions()
        return vars

#classes for control tab
class WPConfModifReviewingControl(WPConfModifReviewingBase):
    """ Tab for reviewing's access control (designing referees, etc.)
    """
    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, target):
        WPConfModifReviewingBase.__init__(self, rh, target)

    def _setActiveTab( self ):
        self._subtabPaperReviewing.setActive()
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
class WPConfModifAbstractsReviewingNotifTplBase( WPConfModifReviewingBase ):

    def _setActiveTab( self ):
        self._tabAbstractNotifTpl.setActive()
        self._subtabAbstractsReviewing.setActive()

class WPConfModifAbstractsReviewingNotifTplList( WPConfModifAbstractsReviewingNotifTplBase ):

    def _getTabContent( self, params ):
        wc = WAbstractsReviewingNotifTpl( self._conf )
        return wc.getHTML()

class WAbstractsReviewingNotifTpl( wcomponents.WTemplated ):
    def __init__( self, conference ):
        self._conf = conference

    def _getNotifTplsHTML(self):
        res=[]
        for tpl in self._conf.getAbstractMgr().getNotificationTplList():
            res.append("""
                <tr>
                    <td bgcolor="white" nowrap>
                        <a href=%s><img src=%s border="0" alt=""></a>
                        <a href=%s><img src=%s border="0" alt=""></a>
                        <input type="checkbox" name="selTpls" value=%s>
                    </td>
                    <td bgcolor="white" align="left" nowrap><a href=%s>%s</a></td>
                    <td>&nbsp;<td>
                    <td bgcolor="white" align="left" width="90%%"><font size="-1">%s</font></td>
                </tr>"""%(quoteattr(str(urlHandlers.UHConfModCFANotifTplUp.getURL(tpl))),\
                            quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))),\
                            quoteattr(str(urlHandlers.UHConfModCFANotifTplDown.getURL(tpl))),\
                            quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))),\
                            quoteattr(str(tpl.getId())), \
                            quoteattr(str(urlHandlers.UHAbstractModNotifTplDisplay.getURL(tpl))), \
                            self.htmlText(tpl.getName()), \
                            self.htmlText(tpl.getDescription())))
        return "".join(res)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["notifTpls"]=self._getNotifTplsHTML()
        vars["addNotifTplURL"]=urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)
        vars["remNotifTplURL"]=urlHandlers.UHAbstractModNotifTplRem.getURL(self._conf)
        return vars

class NotifTplToAddrWrapper:
    _id=""
    _label=""
    _klass=None

    def getId(cls):
        return cls._id
    getId=classmethod(getId)

    def getLabel(cls):
        return _(cls._label)
    getLabel=classmethod(getLabel)

    def getToAddrKlass(cls):
        return cls._klass
    getToAddrKlass=classmethod(getToAddrKlass)

    def addToAddr(cls,tpl):
         tpl.addToAddr(cls._klass())
    addToAddr=classmethod(addToAddr)

    def isSelectedByDefault(cls):
        return False
    isSelectedByDefault = classmethod(isSelectedByDefault)


class NotifTplToAddrSubmitterWrapper(NotifTplToAddrWrapper):

    _id="submitter"
    _klass=review.NotifTplToAddrSubmitter
    _label="Submitters"

    def isSelectedByDefault(cls):
        return True
    isSelectedByDefault = classmethod(isSelectedByDefault)

class NotifTplToAddrPrimaryAuthorsWrapper(NotifTplToAddrWrapper):

    _id="primaryAuthors"
    _label= "Primary authors"
    _klass=review.NotifTplToAddrPrimaryAuthors


class NotifTplToAddrsFactory:

    _avail_toAddrs={
        NotifTplToAddrSubmitterWrapper.getId():NotifTplToAddrSubmitterWrapper,\
        NotifTplToAddrPrimaryAuthorsWrapper.getId():NotifTplToAddrPrimaryAuthorsWrapper}

    def getToAddrList(cls):
        return cls._avail_toAddrs.values()
    getToAddrList=classmethod(getToAddrList)

    def getToAddrById(cls,id):
        return cls._avail_toAddrs.get(id,None)
    getToAddrById=classmethod(getToAddrById)


class WConfModCFANotifTplNew(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def _getErrorHTML(self,errorMsgList):
        if len(errorMsgList)==0:
            return ""
        res=[]
        for error in errorMsgList:
            res.append(self.htmlText(error))
        return """
                <tr align="center">
                    <td bgcolor="white" nowrap colspan="3" style="color:red; padding-bottom:10px; padding-top:10px">
                        <br>
                        <b><font color="red">%s</font></b>
                        <br>
                        <br>
                    </td>
                </tr>"""%"<br>".join(res)

    def _getAvailableTagsHTML(self):
        res=[]
        for var in EmailNotificator.getVarList():
            res.append("""
                <tr class="legendTr">
                    <td width="100%%" nowrap class="blacktext" style="padding-left:10px;padding-right:5px; text-align:left;">|%s|</td>
                    <td class="legendTd" onClick="insertTag('|%s|')">Insert</td>
                </tr>"""%(self.htmlText(var.getName()), self.htmlText(var.getName())))
        return "".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            res.append("""<input name="toAddrs" type="checkbox" value=%s>%s<br>"""%(quoteattr(toAddr.getId()),self.htmlText(toAddr.getLabel())))
        return "&nbsp;".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)))
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        vars["title"]=quoteattr(str(vars.get("title","")))
        vars["description"]=self.htmlText(vars.get("description",""))
        vars["subject"]=quoteattr(str(vars.get("subject","")))
        vars["body"]=self.htmlText(vars.get("body",""))
        vars["fromAddr"]=quoteattr(str(vars.get("fromAddr","")))
        vars["CCAddrs"]=quoteattr(str(",".join(vars.get("ccList",[]))))
        vars["toAddrs"] = self._getToAddrsHTML()
        vars["vars"]=self._getAvailableTagsHTML()
        vars["availableConditions"]= NotifTplConditionsFactory.getConditionList()
        return vars


class WConfModCFANotifTplEditData(wcomponents.WTemplated):

    def __init__(self,notifTpl):
        self._notifTpl=notifTpl

    def _getErrorHTML(self,errorMsgList):
        if len(errorMsgList)==0:
            return ""
        res=[]
        for error in errorMsgList:
            res.append(self.htmlText(error))
        return """
                <tr align="center">
                    <td bgcolor="white" nowrap colspan="3" style="color:red; padding-bottom:10px; padding-top:10px">
                        <br>
                        <b><font color="red">%s</font></b>
                        <br>
                        <br>
                    </td>
                </tr>"""%"<br>".join(res)

    def _getAvailableTagsHTML(self):
        res=[]
        for var in EmailNotificator.getVarList():
            res.append("""
                <tr class="legendTr">
                    <td width="100%%" nowrap class="blacktext" style="padding-left:10px;padding-right:5px; text-align:left;">|%s|</td>
                    <td class="legendTd" onClick="insertTag('|%s|')">Insert</td>
                </tr>"""%(self.htmlText(var.getName()), self.htmlText(var.getName())))
        return "".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            checked = ""
            if self._notifTpl:
                if self._notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                    checked = "checked"
            else:
                if toAddr.isSelectedByDefault():
                    checked = "checked"
            res.append("""<input name="toAddrs" type="checkbox" value=%s %s>%s<br>"""%(quoteattr(toAddr.getId()),checked,self.htmlText(toAddr.getLabel())))
        return "&nbsp;".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplEdit.getURL(self._notifTpl)))
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        if not vars.has_key("title"):
            vars["title"]=quoteattr(str(self._notifTpl.getName()))
        else:
            vars["title"]=quoteattr(str(vars["title"]))
        if not vars.has_key("description"):
            vars["description"]=self.htmlText(self._notifTpl.getDescription())
        else:
            vars["description"]=self.htmlText(vars["description"])
        if not vars.has_key("subject"):
            vars["subject"]=quoteattr(str(self._notifTpl.getTplSubjectShow(EmailNotificator.getVarList())))
        else:
            vars["subject"]=quoteattr(str(vars["subject"]))
        if not vars.has_key("body"):
            vars["body"]=self.htmlText(self._notifTpl.getTplBodyShow(EmailNotificator.getVarList()))
        else:
            vars["body"]=self.htmlText(vars["body"])
        if not vars.has_key("fromAddr"):
            vars["fromAddr"]=quoteattr(str(self._notifTpl.getFromAddr()))
        else:
            vars["fromAddr"]=quoteattr(str(vars["fromAddr"]))
        vars["toAddrs"] = self._getToAddrsHTML()
        if not vars.has_key("ccList"):
            vars["CCAddrs"]=quoteattr(str(",".join(self._notifTpl.getCCAddrList())))
        else:
            vars["CCAddrs"]=quoteattr(str(",".join(vars["ccList"])))
        vars["vars"]=self._getAvailableTagsHTML()
        return vars

class WPModCFANotifTplNew(WPConfModifAbstractsReviewingNotifTplBase):

    def _getTabContent(self,params):
        wc = WConfModCFANotifTplNew(self._conf)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)

    def getJSFiles(self):
        return WPConfModifAbstractsReviewingNotifTplBase.getJSFiles(self) + \
           self._includeJSPackage('Abstracts')

class WPModCFANotifTplBase(WPConfModifReviewingBase):

    def __init__(self, rh, notifTpl):
        WPConfModifReviewingBase.__init__(self, rh, notifTpl.getConference())
        self._notifTpl = notifTpl

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHAbstractModNotifTplDisplay.getURL( self._notifTpl ) )
        self._tabPreview = self._tabCtrl.newTab( "preview", _("Preview"), \
                urlHandlers.UHAbstractModNotifTplPreview.getURL( self._notifTpl ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

#    def _applyFrame( self, body ):
#        frame = wcomponents.WNotifTPLModifFrame( self._notifTpl, self._getAW() )
#        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
#            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
#            "confModifURLGen": urlHandlers.UHConfModifCFA.getURL}
#        return frame.getHTML( body, **p )

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WNotifTplBannerModif(self._notifTpl).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + body

    def _getTabContent( self, params ):
        return "nothing"


class WPModCFANotifTplDisplay(WPModCFANotifTplBase):

    def __init__(self, rh, notifTpl):
        WPModCFANotifTplBase.__init__(self, rh, notifTpl)
        self._conf = self._notifTpl.getConference()

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent(self, params):
        wc = WConfModCFANotifTplDisplay(self._conf, self._notifTpl)
        return wc.getHTML()


class WPModCFANotifTplEdit(WPModCFANotifTplBase):

    def __init__(self, rh, notifTpl):
        WPConferenceModifBase.__init__(self, rh, notifTpl.getConference())
        self._notifTpl=notifTpl


    def _getTabContent(self, params):
        wc=WConfModCFANotifTplEditData(self._notifTpl)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
            self._includeJSPackage('Abstracts')



class WPModCFANotifTplPreview(WPModCFANotifTplBase):

    def _setActiveTab(self):
        self._tabPreview.setActive()

    def _getTabContent(self, params):
        wc = WConfModCFANotifTplPreview(self._notifTpl)
        return wc.getHTML()


class WConfModCFANotifTplPreview(wcomponents.WTemplated):

    def __init__(self,notifTpl):
        self._notifTpl=notifTpl

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        conf=self._notifTpl.getConference()
        if conf.getAbstractMgr().getAbstractList():
            abstract = conf.getAbstractMgr().getAbstractList()[0]
            notif=EmailNotificator().apply(abstract,self._notifTpl)
            vars["from"]=notif.getFromAddr()
            vars["to"]=notif.getToList()
            vars["cc"]=notif.getCCList()
            vars["subject"]=notif.getSubject()
            vars["body"] = notif.getBody()
        else:
            vars["from"] = _("""<center> _("No preview avaible")</center>""")
            vars["to"] = _("""<center> _("No preview avaible")</center>""")
            vars["cc"]= _("""<center> _("No preview avaible")</center>""")
            vars["subject"] = _("""<center> _("No preview avaible")</center>""")
            vars["body"] = _("""<center> _("An abstract must be submitted to display the preview")</center>""")
        vars["cfaURL"]=quoteattr(str(urlHandlers.UHConfModifCFA.getURL(conf)))
        return vars

class NotifTplConditionWrapper:
    _id=""
    _label=""
    _klass=None

    def getId(cls):
        return cls._id
    getId=classmethod(getId)

    def getLabel(cls):
        return _(cls._label)
    getLabel=classmethod(getLabel)

    def getConditionKlass(cls):
        return cls._klass
    getConditionKlass=classmethod(getConditionKlass)

    def addCondition(cls,tpl,**data):
        pass
    addCondition=classmethod(addCondition)

    def needsDialog(cls,**data):
        return False
    needsDialog=classmethod(needsDialog)

    def getDialogKlass(cls):
        return None
    getDialogKlass=classmethod(getDialogKlass)


class NotifTplCondAcceptedWrapper(NotifTplConditionWrapper):

    _id="accepted"
    _label= _("in status ACCEPTED")
    _klass=review.NotifTplCondAccepted

    @classmethod
    def addCondition(cls,tpl,**data):
        cType=data.get("contribType","--any--")
        t=data.get("track","--any--")
        tpl.addCondition(cls._klass(track=t,contribType=cType))

    @classmethod
    def needsDialog(cls,**data):
        if data.has_key("contribType") and data["contribType"]!="":
            return False
        return True

    @classmethod
    def getDialogKlass(cls):
        return WPModNotifTplCondAcc


class NotifTplCondRejectedWrapper(NotifTplConditionWrapper):

    _id="rejected"
    _label= _("in status REJECTED")
    _klass=review.NotifTplCondRejected

    @classmethod
    def addCondition(cls,tpl,**data):
        tpl.addCondition(cls._klass())

class NotifTplCondMergedWrapper(NotifTplConditionWrapper):

    _id="merged"
    _label= _("in status MERGED")
    _klass=review.NotifTplCondMerged

    @classmethod
    def addCondition(cls,tpl,**data):
        tpl.addCondition(cls._klass())


class NotifTplConditionsFactory:

    _avail_conds={
        NotifTplCondAcceptedWrapper.getId():NotifTplCondAcceptedWrapper,\
        NotifTplCondRejectedWrapper.getId():NotifTplCondRejectedWrapper,\
        NotifTplCondMergedWrapper.getId():NotifTplCondMergedWrapper}

    def getConditionList(cls):
        return cls._avail_conds.values()
    getConditionList=classmethod(getConditionList)

    def getConditionById(cls,id):
        return cls._avail_conds.get(id,None)
    getConditionById=classmethod(getConditionById)


class WConfModNotifTplCondAcc(wcomponents.WTemplated):

    def __init__(self,tpl):
        self._notifTpl=tpl

    def _getContribTypeItemsHTML(self):
        res=["""<option value="--any--">--any--</option>""",
                """<option value="--none--">--none--</option>"""]
        for t in self._notifTpl.getConference().getContribTypeList():
            res.append("""<option value=%s>%s</option>"""%(quoteattr(t.getId()),self.htmlText(t.getName())))
        return "".join(res)

    def _getTrackItemsHTML(self):
        res=["""<option value="--any--">--any--</option>""",
                """<option value="--none--">--none--</option>"""]
        for t in self._notifTpl.getConference().getTrackList():
            res.append("""<option value=%s>%s</option>"""%(quoteattr(t.getId()),self.htmlText(t.getTitle())))

        return "".join(res)
    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=urlHandlers.UHConfModNotifTplConditionNew.getURL(self._notifTpl)
        vars["condType"]=quoteattr(str(NotifTplCondAcceptedWrapper.getId()))
        vars["contribTypeItems"]=self._getContribTypeItemsHTML()
        vars["trackItems"]=self._getTrackItemsHTML()
        return vars


class WPModNotifTplCondAcc(WPModCFANotifTplBase):

    def _getTabContent( self, params ):
        wc=WConfModNotifTplCondAcc(self._notifTpl)
        return wc.getHTML()


class WConfModCFANotifTplDisplay(wcomponents.WTemplated):

    def __init__(self, conf, notifTpl):
        self._conf = conf
        self._notifTpl = notifTpl

    def _getConditionItemsHTML(self):
        res=[]
        for cond in NotifTplConditionsFactory.getConditionList():
            res.append("<option value=%s>%s</option>"""%(quoteattr(cond.getId()),self.htmlText(cond.getLabel())))
        return "".join(res)

    def _getConditionsHTML(self):
        res=[]
        for cond in self._notifTpl.getConditionList():
            caption=""
            if isinstance(cond,review.NotifTplCondAccepted):
                track=cond.getTrack()
                if track is None or track=="":
                    track="--none--"
                elif track not in ["--none--","--any--"]:
                    track=track.getTitle()
                cType=cond.getContribType()
                if cType is None or cType=="":
                    cType="--none--"
                elif cType not in ["--none--","--any--"]:
                    cType=cType.getName()
                caption= _("""ACCEPTED - type: %s - track: %s""")%(self.htmlText(cType),self.htmlText(track))
            elif isinstance(cond,review.NotifTplCondRejected):
                caption= _("""REJECTED""")
            elif isinstance(cond,review.NotifTplCondMerged):
                caption= _("""MERGED""")
            res.append(""" <input type="image" src="%s" onclick="javascript:this.form.selCond.value = '%s'; this.form.submit();return false;"> %s"""%(Config.getInstance().getSystemIconURL( "remove" ), cond.getId(), caption))
        return "<br>".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            if self._notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                res.append("%s"%self.htmlText(toAddr.getLabel()))
        return ", ".join(res)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["name"] = self._notifTpl.getName()
        vars["description"] = self._notifTpl.getDescription()
        vars["from"] = self._notifTpl.getFromAddr()
        vars["toAddrs"] = self._getToAddrsHTML()
        vars["CCAddrs"]=",".join(self._notifTpl.getCCAddrList())
        vars["subject"] = self._notifTpl.getTplSubjectShow(EmailNotificator.getVarList())
        vars["body"] = self._notifTpl.getTplBodyShow(EmailNotificator.getVarList())
        vars["conditions"]=self._getConditionsHTML()
        vars["availableConditions"]=self._getConditionItemsHTML()
        vars["remConditionsURL"]=quoteattr(str(urlHandlers.UHConfModNotifTplConditionRem.getURL(self._notifTpl)))
        vars["newConditionURL"]=quoteattr(str(urlHandlers.UHConfModNotifTplConditionNew.getURL(self._notifTpl)))
        vars["modifDataURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplEdit.getURL(self._notifTpl)))
        return vars



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

        if self._conf.getConfPaperReview().getChoice() != 1 and self._conf.getConfPaperReview().getChoice() == 0:
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

        vars["Conference"] = self.__target.getId()
        vars["ConfReview"] = self.__target.getConfPaperReview()
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

        vars["Conference"] = self.__target.getId()
        vars["ConfReview"] = self.__target.getConfPaperReview()
        return vars

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
        vars["abstractManagerTable"] = wcomponents.WPrincipalTable().getHTML( self.__target.getConfPaperReview().getAbstractManagersList(),
                                                                              self.__target, vars["addAbstractManagerURL"],
                                                                              vars["removeAbstractManagerURL"], selectable=False)
        vars["abstractReviewerTable"] = wcomponents.WPrincipalTable().getHTML( self.__target.getConfPaperReview().getAbstractReviewersList(),
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
        self._subtabPaperReviewing.setActive()
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
        self._subtabPaperReviewing.setActive()
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
        vars["ConfReview"] = self._conf.getConfPaperReview()

        return vars