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

from datetime                       import datetime
from flask import session
from MaKaC.webinterface             import wcomponents,urlHandlers
from MaKaC.webinterface.wcomponents import WUtils
from MaKaC.webinterface.pages       import conferences
from xml.sax.saxutils               import quoteattr
from MaKaC.evaluation               import Evaluation,Question,Box,Choice,Textbox,Textarea,Password,Select,Radio,Checkbox,Submission
from MaKaC.webinterface.navigation  import NEEvaluationMainInformation,NEEvaluationDisplay,NEEvaluationDisplayModif
from MaKaC.errors                   import FormValuesError
from MaKaC.common                   import utils
from MaKaC.user                     import Avatar
from MaKaC.i18n                     import _
from indico.util.i18n import i18nformat
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase

from indico.core.config import Config

##############
#Display Area#
##############


class WPEvaluationBase( conferences.WPConferenceDefaultDisplayBase ):
    """[DisplayArea] Base class."""
    pass

class WPEvaluationMainInformation( WPEvaluationBase ):
    """[DisplayArea] display evaluation general information."""
    navigationEntry = NEEvaluationMainInformation

    def _getBody(self, params):
        return WEvaluationMainInformation(self._conf, self._getAW().getUser()).getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._evaluationOpt)


class WEvaluationMainInformation(WConfDisplayBodyBase):
    """[DisplayArea] display evaluation general information."""

    _linkname = "evaluation"

    def __init__(self, conf, user):
        self._conf = conf
        self._user = user

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        evaluation = self._conf.getEvaluation()
        wvars["body_title"] = self._getTitle()
        wvars["startDate"] = evaluation.getStartDate().strftime("%d %B %Y")
        wvars["endDate"] = evaluation.getEndDate().strftime("%d %B %Y")
        wvars["announcement"] = evaluation.getAnnouncement()
        wvars["title"] = evaluation.getTitle()
        wvars["submissionsLimit"] = evaluation.getSubmissionsLimit()
        wvars["contactInfo"] = evaluation.getContactInfo()
        #actions
        wvars["actionsShow"] = evaluation.inEvaluationPeriod()
        wvars["actionsDisplayEval"] = None
        wvars["actionsModifyEval"] = None
        if wvars["actionsShow"]:
            if self._user != None and self._user.hasSubmittedEvaluation(evaluation):
                wvars["actionsModifyEval"] = urlHandlers.UHConfEvaluationDisplayModif.getURL(self._conf)
            else:
                wvars["actionsDisplayEval"] = urlHandlers.UHConfEvaluationDisplay.getURL(self._conf)
        return wvars


class WPEvaluationDisplay( WPEvaluationBase ):
    """[DisplayArea] Evaluation default display."""
    navigationEntry = NEEvaluationDisplay

    def _getBody(self, params):
        pars = {
            'user': self._rh._getUser()
        }
        return WEvaluationDisplay(self._conf).getHTML(pars)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._newEvaluationOpt)


class WEvaluationDisplay(WConfDisplayBodyBase):
    """[DisplayArea] Evaluation default display."""

    _linkname = "newEvaluation"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["evaluation"] = self._conf.getEvaluation()
        user = wvars["user"]
        wvars["hasSubmittedEvaluation"] = isinstance(user,Avatar) and user.hasSubmittedEvaluation(self._conf.getEvaluation())
        wvars["actionUrl"] = urlHandlers.UHConfEvaluationSubmit.getURL(self._conf, mode=Evaluation._SUBMIT)
        return wvars


class WPEvaluationDisplayModif( WPEvaluationBase ):
    """[DisplayArea] The user modifies his already submitted evaluation."""
    navigationEntry = NEEvaluationDisplayModif

    def _getBody(self, params):
        pars = {
            'user': self._rh._getUser()
        }
        return WEvaluationDisplayModif(self._conf).getHTML(pars)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._viewEvaluationOpt)


class WEvaluationDisplayModif(WEvaluationDisplay):
    """[DisplayArea] The user modifies his already submitted evaluation."""

    _linkname = "viewMyEvaluation"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = WEvaluationDisplay.getVars(self)
        vars["body_title"] = self._getTitle()
        vars["actionUrl"] = urlHandlers.UHConfEvaluationSubmit.getURL(self._conf, mode=Evaluation._EDIT)
        return vars


class WPEvaluationSubmitted( WPEvaluationBase ):
    """[DisplayArea] Submitted Evaluation."""
    navigationEntry = NEEvaluationMainInformation

    def __init__(self, rh, conf, mode):
        self._mode = mode
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)

    def _getBody(self, params):
        pars = {}
        # redirection
        if self._rh.getWebFactory() is not None:  #Event == Meeting/Lecture
            pars["redirection"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        else:  #Event == Conference
            pars["redirection"] = None
        return WEvaluationSubmitted(self._conf, self._mode).getHTML(pars)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._evaluationOpt)


class WEvaluationSubmitted(WEvaluationDisplay):
    """Submitted Evaluation."""

    _linkname = "newEvaluation"

    def __init__(self, conference, mode=Evaluation._SUBMIT):
        self._conf = conference
        self._mode = mode

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        if not wvars.has_key("redirection"):
            wvars["redirection"] = None
        if self._mode == Evaluation._SUBMIT:
            wvars["status"] = _("submitted")
        elif self._mode == Evaluation._EDIT:
            wvars["status"] = _("modified")
        else:  # should never be here...
            if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
                raise Exception(_("Evaluation - Possible modes are %s, given : %s.") % (
                                [Evaluation._SUBMIT, Evaluation._EDIT], self._mode))
            else:
                wvars["status"] = _("submitted")
        return wvars


class WPEvaluationFull( WPEvaluationBase ):
    """[DisplayArea] Evaluation is full."""
    navigationEntry = NEEvaluationDisplay

    def _getBody( self, params ):
        return WEvaluationFull(self._conf).getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._evaluationOpt)


class WEvaluationFull(WEvaluationDisplay):
    """[DisplayArea] Evaluation is full."""

    _linkname = "evaluation"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["limit"] = self._conf.getEvaluation().getSubmissionsLimit()
        return wvars


class WPEvaluationClosed( WPEvaluationBase ):
    """[DisplayArea] Evaluation is closed."""
    navigationEntry = NEEvaluationDisplay

    def _getBody( self, params ):
        return WEvaluationClosed(self._conf).getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._evaluationOpt)


class WEvaluationClosed(WEvaluationDisplay):
    """[DisplayArea] Evaluation is closed."""

    _linkname = "evaluation"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        evaluation = self._conf.getEvaluation()
        sDate = evaluation.getStartDate()
        eDate = evaluation.getEndDate()

        wvars["body_title"] = self._getTitle()
        wvars["msg"] = _("No period for evaluation:")
        if nowutc() < sDate:
            wvars["msg"] = _("Sorry, but the evaluation is not open yet.")
        elif nowutc() > eDate:
            wvars["msg"] = _("Sorry, but the evaluation period has finished.")
        wvars["startDate"] = sDate.strftime("%A %d %B %Y")
        wvars["endDate"] = eDate.strftime("%A %d %B %Y")
        return wvars


class WPEvaluationSignIn( WPEvaluationBase ):
    """[DisplayArea] Invite user to login/signin."""
    navigationEntry = NEEvaluationDisplay

    def _getBody( self, params ):
        return WEvaluationSignIn( self._conf ).getHTML(params)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._newEvaluationOpt)

class WEvaluationSignIn(wcomponents.WTemplated):
    """[DisplayArea] Invite user to login/signin."""

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["signInURL"] = urlHandlers.UHConfSignIn.getURL(self._conf, urlHandlers.UHConfEvaluationDisplay.getURL(self._conf))
        return vars


class WPEvaluationInactive( WPEvaluationBase ):
    """[DisplayArea] Inactive evaluation."""

    def _getBody( self, params ):
        return WEvaluationInactive(self._conf).getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._evaluationOpt)


class WEvaluationInactive(WEvaluationDisplay):
    """[DisplayArea] Inactive evaluation."""

    _linkname = "evaluation"

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


#################
#Management Area#
#################


class WPConfModifEvaluationBase( conferences.WPConferenceModifBase ):
    """[ManagementArea] Base class."""

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        self._tabEvaluationSetup = self._tabCtrl.newTab( "evaluationsetup", _("Setup"), \
                urlHandlers.UHConfModifEvaluationSetup.getURL( self._conf ) )
        self._tabEvaluationEdit = self._tabCtrl.newTab( "edit", _("Edit"), \
                urlHandlers.UHConfModifEvaluationEdit.getURL( self._conf ) )
        self._tabEvaluationPreview = self._tabCtrl.newTab( "preview", _("Preview"), \
                urlHandlers.UHConfModifEvaluationPreview.getURL( self._conf ) )
        self._tabEvaluationResults = self._tabCtrl.newTab( "results", _("Results"), \
                urlHandlers.UHConfModifEvaluationResults.getURL( self._conf ) )
        if not self._conf.hasEnabledSection("evaluation"):
            self._tabEvaluationSetup.disable()
            self._tabEvaluationEdit.disable()
            self._tabEvaluationPreview.disable()
            self._tabEvaluationResults.disable()
        self._setActiveTab()

    def _setActiveTab( self ):
        self._tabEvaluationEdit.disable()

    def _setActiveSideMenuItem( self ):
        self._evaluationMenuItem.setActive()

    def _getPageContent( self, params ):
        self._createTabCtrl()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return html

    def _getTabContent( self, params ):
        return  _("nothing")


class WPConfModifEvaluationSetup( WPConfModifEvaluationBase ):
    """[ManagementArea] Modification of an Evaluation."""

    def _getTabContent( self, params ):
        return WConfModifEvaluationSetup(self._conf).getHTML()

    def _setActiveTab( self ):
        self._tabEvaluationSetup.setActive()

class WConfModifEvaluationSetup( wcomponents.WTemplated ):
    """[ManagementArea] Modification of an Evaluation."""

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        from MaKaC.registration import Notification
        vars = wcomponents.WTemplated.getVars(self)
        evaluation = self._conf.getEvaluation()
        evaluationStartNotification = evaluation.getNotification(Evaluation._EVALUATION_START)
        newSubmissionNotification   = evaluation.getNotification(Evaluation._NEW_SUBMISSION)
        vars["setStatusURL"]=urlHandlers.UHConfModifEvaluationSetupChangeStatus.getURL(self._conf)
        vars["dataModificationURL"]=urlHandlers.UHConfModifEvaluationDataModif.getURL(self._conf)
        vars["specialActionURL"] = urlHandlers.UHConfModifEvaluationSetupSpecialAction.getURL(self._conf)
        vars["evaluation"] = evaluation
        vars["submissionsLimit"] = i18nformat("""--_("No limit")--""")
        if evaluation.getSubmissionsLimit() > 0:
            vars["submissionsLimit"] = evaluation.getSubmissionsLimit()
        vars["title"] = evaluation.getTitle()
        if evaluation.isMandatoryParticipant():
            vars["mandatoryParticipant"] = _("Yes")
        else:
            vars["mandatoryParticipant"] = _("No")
        if evaluation.isMandatoryAccount():
            vars["mandatoryAccount"] = _("Yes")
        else:
            vars["mandatoryAccount"] = _("No")
        if evaluation.isAnonymous() :
            vars["anonymous"] = _("Yes")
        else:
            vars["anonymous"] = _("No")
        if evaluationStartNotification == None :
            vars["evaluationStartNotifyTo"] = ""
            vars["evaluationStartNotifyCc"] = ""
        else :
            vars["evaluationStartNotifyTo"] = ", ".join(evaluationStartNotification.getToList())
            vars["evaluationStartNotifyCc"] = ", ".join(evaluationStartNotification.getCCList())
        if newSubmissionNotification == None :
            vars["newSubmissionNotifyTo"] = ""
            vars["newSubmissionNotifyCc"] = ""
        else :
            vars["newSubmissionNotifyTo"]   = ", ".join(newSubmissionNotification.getToList())
            vars["newSubmissionNotifyCc"]   = ", ".join(newSubmissionNotification.getCCList())
        ##############
        #if activated#
        ##############
        if evaluation.isVisible():
            vars["changeTo"] = "False"
            vars["status"] = _("VISIBLE")
            if evaluation.getNbOfQuestions()<1 :
                vars["statusMoreInfo"] = i18nformat("""<span style="color: #E25300">(_("not ready"))</span>""")
            elif nowutc() < evaluation.getStartDate() :
                vars["statusMoreInfo"] = i18nformat("""<span style="color: #E25300">(_("not open yet"))</span>""")
            elif nowutc() > evaluation.getEndDate() :
                vars["statusMoreInfo"] = i18nformat("""<span style="color: #E25300">(_("closed"))</span>""")
            else:
                vars["statusMoreInfo"] = i18nformat("""<span style="color: green">(_("running"))</span>""")
            vars["changeStatus"] = _("HIDE")
            if evaluation.getStartDate() is None:
                vars["startDate"] = ""
            else:
                vars["startDate"] = evaluation.getStartDate().strftime("%A %d %B %Y")
            if evaluation.getEndDate() is None:
                vars["endDate"] = ""
            else:
                vars["endDate"] = evaluation.getEndDate().strftime("%A %d %B %Y")
        ################
        #if deactivated#
        ################
        else:
            vars["changeTo"] = "True"
            vars["status"] = _("HIDDEN")
            vars["statusMoreInfo"] = ""
            vars["changeStatus"] = _("SHOW")
            vars["startDate"] = ""
            vars["endDate"] = ""
        return vars


class WPConfModifEvaluationSetupImportXml( WPConfModifEvaluationSetup ):
    """[ManagementArea] Import an evaluation from an XML file."""

    def _getTabContent( self, params ):
        return WConfModifEvaluationSetupImportXml(self._conf).getHTML()

class WConfModifEvaluationSetupImportXml( WConfModifEvaluationSetup ):
    """[ManagementArea] Import an evaluation from an XML file."""

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        evaluation = self._conf.getEvaluation()
        vars["actionUrl"] = urlHandlers.UHConfModifEvaluationSetupSpecialAction.getURL(self._conf)
        return vars


class WPConfModifEvaluationSetupDataModif( WPConfModifEvaluationSetup ):
    """[ManagementArea] called when you want to change general parameters of your evaluation."""

    def _getTabContent( self, params ):
        return WConfModifEvaluationSetupDataModif(self._conf).getHTML()

class WConfModifEvaluationSetupDataModif( WConfModifEvaluationSetup ):
    """[ManagementArea] change general parameters of your evaluation."""

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        from MaKaC.registration import Notification
        from MaKaC.webinterface.webFactoryRegistry import WebFactoryRegistry
        vars = wcomponents.WTemplated.getVars(self)
        evaluation = self._conf.getEvaluation()
        evaluationStartNotification = evaluation.getNotification(Evaluation._EVALUATION_START)
        newSubmissionNotification   = evaluation.getNotification(Evaluation._NEW_SUBMISSION)
        vars["postURL"]=urlHandlers.UHConfModifEvaluationPerformDataModif.getURL(self._conf)
        vars["announcement"]     = evaluation.getAnnouncement()
        vars["contactInfo"]      = evaluation.getContactInfo()
        vars["submissionsLimit"] = evaluation.getSubmissionsLimit()
        vars["title"]            = evaluation.getTitle()
        if evaluation.getStartDate() is None:
            vars["sDay"]  =""
            vars["sMonth"]=""
            vars["sYear"] =""
        else:
            d = evaluation.getStartDate()
            vars["sDay"]  =str(d.day)
            vars["sMonth"]=str(d.month)
            vars["sYear"] =str(d.year)
        if evaluation.getEndDate() is None:
            vars["eDay"]  =""
            vars["eMonth"]=""
            vars["eYear"] =""
        else:
            d = evaluation.getEndDate()
            vars["eDay"]  = str(d.day)
            vars["eMonth"]= str(d.month)
            vars["eYear"] = str(d.year)
        if evaluation.isMandatoryAccount():
            vars["mandatoryAccount"]='checked'
        else:
            vars["mandatoryAccount"]=""
        if evaluation.isMandatoryParticipant():
            vars["mandatoryParticipant"]='checked'
        else:
            vars["mandatoryParticipant"]=""
        if evaluation.isAnonymous() :
            vars["anonymous"] = 'checked'
        else:
            vars["anonymous"] = ""
        #Notifications
        if WebFactoryRegistry().getFactory(self._conf)==None: #Conference
            vars["adherent"] = "registrant"
            allAdherents = [r.getEmail() for r in self._conf.getRegistrantsList()]
        else : #Lecture / Meeting
            vars["adherent"] = "participant"
            allAdherents = [p.getEmail() for p in self._conf.getParticipation().getParticipantList()]
        if evaluationStartNotification == None :
            vars["evaluationStartNotifyTo"] = ""
            vars["evaluationStartNotifyCc"] = ""
        else :
            toList = evaluationStartNotification.getToList()
            vars["evaluationStartNotifyTo"] = ", ".join(toList)
            vars["evaluationStartNotifyCc"] = ", ".join(evaluationStartNotification.getCCList())
        if newSubmissionNotification == None :
            vars["newSubmissionNotifyTo"] = ""
            vars["newSubmissionNotifyCc"] = ""
        else :
            vars["newSubmissionNotifyTo"]   = ", ".join(newSubmissionNotification.getToList())
            vars["newSubmissionNotifyCc"]   = ", ".join(newSubmissionNotification.getCCList())
        return vars



class WPConfModifEvaluationEdit( WPConfModifEvaluationBase ):
    """[ManagementArea] Edition of Evaluation questions."""

    def _getTabContent( self, params ):
        return WConfModifEvaluationEdit(self._conf).getHTML(self._rh.getRequestParams())

    def _setActiveTab( self ):
        self._tabEvaluationEdit.setActive()

class WConfModifEvaluationEdit( wcomponents.WTemplated ):
    """[ManagementArea] General frame for editing Evaluation questions."""

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        ###########
        #variables#
        ###########
        vars = wcomponents.WTemplated.getVars(self)
        mode = vars.get("mode","")              #actual mode (add, edit, ...)
        error = vars.get("error","")            #error message
        questionType = vars.get("type","")      #which question type is selected
        questionPos = int(vars.get("questionPos",-1)) #position of selected question, used when mode is EDIT.

        ###########
        #left menu#
        ###########
        self._leftMenu(questionType, vars)

        ######
        #main#
        ######
        if mode==Question._ADD:
            if questionType not in Question._QUESTION_SUBTYPES:
                raise FormValuesError( _("Unknown question type !"), _("Evaluation"))
            vars["main"] = WConfModifEvaluationEditQuestion(self._conf, mode, error, questionType, None).getHTML()
        elif mode==Question._EDIT:
            question = self._conf.getEvaluation().getQuestionAt(questionPos)
            if question == None:
                raise FormValuesError( _("No question found at the given position!"), _("Evaluation"))
            else:
                questionType = question.getTypeName()
                vars["main"] = WConfModifEvaluationEditQuestion(self._conf, mode, error, questionType, question).getHTML()
        else:
            #When no mode is selected, by default it shows the global view of questions.
            vars["main"] = ""
            for q in self._conf.getEvaluation().getQuestions():
                vars["main"] += str(WConfModifEvaluationEditQuestionView(q).getHTML())
        return vars

    def _leftMenu(self, questionType, vars):
        """ create left menu of the webpage. Be aware that 'vars' is mutable.
            Params:
                questionType -- type of the question selected
                vars -- dictionnary containing all parameters used for templating"""
        #generate links
        url_tbox = urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf, mode=Question._ADD, type=Question._TEXTBOX)
        url_area = urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf, mode=Question._ADD, type=Question._TEXTAREA)
        url_pswd = urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf, mode=Question._ADD, type=Question._PASSWORD)
        url_slct = urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf, mode=Question._ADD, type=Question._SELECT)
        url_radi = urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf, mode=Question._ADD, type=Question._RADIO)
        url_chck = urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf, mode=Question._ADD, type=Question._CHECKBOX)
        #creates all buttons in the left menu
        vars["form_tbox"]= self._createQuestionImgButton(url_tbox, questionType, Question._TEXTBOX)
        vars["form_area"]= self._createQuestionImgButton(url_area, questionType, Question._TEXTAREA)
        vars["form_pswd"]= self._createQuestionImgButton(url_pswd, questionType, Question._PASSWORD)
        vars["form_slct"]= self._createQuestionImgButton(url_slct, questionType, Question._SELECT)
        vars["form_radi"]= self._createQuestionImgButton(url_radi, questionType, Question._RADIO)
        vars["form_chck"]= self._createQuestionImgButton(url_chck, questionType, Question._CHECKBOX)

    def _createQuestionImgButton(self, url, questionType, qType):
        """ Depending on selected questionType it creates changing button or fixed image.
            This short function is just a shortcut.
            See WUtils.createChangingImgButton() and WUtils.createImg() for more details...
        """
        imgID    = "form_"+qType
        imgOverID= "form_"+qType+"_"
        info     = _("Insert a question of type ")+qType
        if questionType==qType:
            return WUtils.createImg(imgOverID, info)
        else:
            return WUtils.createChangingImgButton(url, imgID, imgOverID, info)

class WConfModifEvaluationEditQuestionView( wcomponents.WTemplated ):
    """[ManagementArea] This is the presentation of a question when editing the whole evaluation form structure."""

    def __init__( self, question ):
        self._question = question

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        conf = self._question.getEvaluation().getConference()
        #required
        if self._question.isRequired():
            vars["required"] = "* "
        else:
            vars["required"] = ""
        #questionValue, keyword, description, help
        vars["questionValue"]= self._question.getQuestionValue()
        vars["keyword"]      = self._question.getKeyword()
        vars["description"]  = self._question.getDescription()
        vars["help"]         = self._question.getHelp()
        #question input
        vars["input"] = self._question.displayHtml(disabled="disabled")
        #actionUrl for change position + edit question
        url = urlHandlers.UHConfModifEvaluationEditPerformChanges.getURL(conf)
        url.addParam("mode", Question._EDIT)
        vars["actionUrl"] = url
        #change question position select
        posName     = "posChange_%s"%(self._question.getPosition())
        nbQuestions = self._question.getEvaluation().getNbOfQuestions()
        questionPos = self._question.getPosition()
        vars["posChange"] = WUtils.createSelect(False, range(1,nbQuestions+1), questionPos, name=posName, onchange="this.form.submit()")
        #actual position
        vars["actualPosition"] = self._question.getPosition()
        #modifiy question
        url = urlHandlers.UHConfModifEvaluationEdit.getURL(conf, mode=Question._EDIT, questionPos=questionPos)
        vars["editQuestion"] = WUtils.createImgButton(url, "edit", "edit")
        #remove question
        url = urlHandlers.UHConfModifEvaluationEditPerformChanges.getURL(conf, mode=Question._REMOVE, questionPos=questionPos)
        vars["removeQuestionUrl"] = url
        vars["removeQuestionInput"] = WUtils.createInput(type="image",
                                                         name="remove",
                                                         id="questionRemove%s" % self._question.getPosition(),
                                                         alt="remove",
                                                         src=Config.getInstance().getSystemIconURL("remove"))
        #return
        return vars

class WConfModifEvaluationEditQuestion( wcomponents.WTemplated ):
    """[ManagementArea] Edition of one particular Evaluation question."""

    #constant for function _choiceItems()
    _CHOICEITEMS_NB_MIN = 2

    def __init__( self, conference, mode, error, questionType, question ):
        """Params:
            conference -- current conference (obvious!).
            mode -- actual mode (add, edit, ...).
            error -- error message.
            questionType -- which question type is selected.
            question -- question being edited, only used when the mode is EDIT.
        """
        self._conf = conference
        self._evaluation = self._conf.getEvaluation()
        self._mode = mode
        self._error = error
        self._questionType = questionType
        self._question = question

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        nbQuestions = self._evaluation.getNbOfQuestions()
        #actionUrl
        url = urlHandlers.UHConfModifEvaluationEditPerformChanges.getURL(self._conf, mode=self._mode)

        ###########
        #Edit mode#
        ###########
        if self._mode == Question._EDIT:
            url.addParam("questionPos", self._question.getPosition())
            if self._question.isRequired():
                vars["required"] = 'checked="checked"'
            else:
                vars["required"] = ""
            vars["questionValue"]= self._question.getQuestionValue()
            vars["keyword"]      = self._question.getKeyword()
            vars["description"]  = self._question.getDescription()
            vars["help"]         = self._question.getHelp()
            vars["position"]     = WUtils.createSelect(False,
                                                       range(1,nbQuestions+1),
                                                       self._question.getPosition(),
                                                       name="newPos")
            vars["saveButtonText"] = _("modify question")
            vars["choiceItems"]  = self._choiceItems(self._question);
            if self._questionType in Question._BOX_SUBTYPES:
                defaultAnswer    = self._question.getDefaultAnswer()
            else: #Unused, but : Better to prevent than to heal!
                defaultAnswer    = ""
            url.addParam("questionPos",self._question.getPosition())

        ##########
        #Add mode#
        ##########
        else:
            url.addParam("type", self._questionType)
            vars["required"]     = ""
            vars["questionValue"]= ""
            vars["keyword"]      = ""
            vars["description"]  = ""
            vars["help"]         = ""
            vars["position"]     = WUtils.createSelect(False,
                                                       range(1,nbQuestions+2),
                                                       nbQuestions+1,
                                                       name="newPos")
            vars["saveButtonText"]= _("add question")
            vars["choiceItems"]   = self._choiceItems();
            defaultAnswer         = ""

        #######
        #Other#
        #######
        #defaultAnswer
        if self._questionType in Question._BOX_SUBTYPES:
            vars["defaultAnswer"] = i18nformat("""<tr>
                    <td class="titleCellTD"><span class="titleCellFormat">  _("Default answer")</span></td>
                    <td class="inputCelTD"><input type="text" name="defaultAnswer" value="%s"/></td>
                </tr>""")%(defaultAnswer)
        else:
            vars["defaultAnswer"] = ""
        #javascript for choiceItems
        vars["choiceItemsNb"] = self._CHOICEITEMS_NB_MIN
        vars["javascriptChoiceItemsAddImg"] = WUtils.createImg("add", _("add one more choice item")).replace('"',"'")
        vars["javascriptChoiceItemsRemoveImg"] = WUtils.createImg("remove", _("remove one choice item")).replace('"',"'")
        if self._questionType == Question._CHECKBOX:
            vars["javascriptChoiceItemsType"] = "checkbox"
        elif self._questionType in [Question._SELECT, Question._RADIO]:
            vars["javascriptChoiceItemsType"] = "radio"
        else:
            vars["javascriptChoiceItemsType"] = ""
        #error
        if self._error!="":
            vars["error"] = "%s<br/><br/><br/>"%(self._error)
        else:
            vars["error"] = ""
        #actionUrl
        vars["actionUrl"] = url
        return vars

    def _choiceItems(self, question=None):
        """ generates HTML code for showing the choice items.
            Params:
                question -- (optional) object of type Question.
        """
        #check
        if self._questionType not in Question._CHOICE_SUBTYPES:
            return ""
        #choice items
        if isinstance(question, Choice):
            choiceItemsNb = question.getNbOfChoiceItems()
        else:
            choiceItemsNb = self._CHOICEITEMS_NB_MIN
        #depending on question type...
        if self._questionType == Question._CHECKBOX:
            type = "checkbox"
        elif self._questionType in [Question._SELECT, Question._RADIO]:
            type = "radio"
        #images
        addImg = WUtils.createImg("add", _("add one more choice item"))
        removeImg = WUtils.createImg("remove", _("remove one choice item"))
        ##############################################################################
        #return HTML string when question is a Choice (e.g. Checkbox, Select, Radio).#
        ##############################################################################
        html = "%s"
        #I insert <span> with <input>s for each choice item.
        for i in range(1, choiceItemsNb+1):
            #play with choice items
            itemText = ""
            isSelected = ""
            if question!=None and i<=choiceItemsNb:
                itemText = question.getChoiceItemsKeyAt(i)
                isSelected = question.getChoiceItemsCorrespondingValue(itemText)
                if isSelected == True:
                    isSelected = "checked='checked'"
                else:
                    isSelected = ""
            #play with html text
            htmlInsert = """<span id='field_"""+str(i)+"""'>
                          <input type='"""+type+"""' name='selectedChoiceItems' value='"""+str(i)+"""' """+isSelected+"""/>
                          <input name='choiceItem_"""+str(i)+"""' type='text' class='choiceItemText' value=\""""+itemText+"""\"/><br/>
                          %s
                        </span>"""
            html = html%(htmlInsert)
        #I finally insert the span containing links for adding/removing a choice item.
        htmlInsert= """<span id='field_"""+str(choiceItemsNb+1)+"""'>
                        <a href='javascript:addField("""+str(choiceItemsNb+1)+""")' style='padding-left:40px;'>
                          """+addImg+"""
                        </a>
                        <a href='javascript:removeField("""+str(choiceItemsNb)+""")'>
                          """+removeImg+"""
                        </a>
                      </span>"""
        html = html%(htmlInsert)
        return html



class WPConfModifEvaluationPreview( WPConfModifEvaluationBase ):
    """[ManagementArea] Preview of an Evaluation."""
    def _getTabContent( self, params ):
        pars = {
            'user': self._rh._getUser()
        }
        return WConfModifEvaluationPreview(self._conf).getHTML(pars)
    def _setActiveTab( self ):
        self._tabEvaluationPreview.setActive()

class WConfModifEvaluationPreview( WEvaluationDisplay ):
    """[ManagementArea] Preview of an Evaluation."""

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = WEvaluationDisplay.getVars(self)
        vars["hasSubmittedEvaluation"] = False
        vars["actionUrl"] = urlHandlers.UHConfModifEvaluationPreview.getURL(self._conf, status=_("submitted"))
        return vars


class WPConfModifEvaluationPreviewSubmitted( WPConfModifEvaluationBase ):
    """[ManagementArea] Preview of an Evaluation when it has been submitted."""
    def _getTabContent( self, params ):
        return WEvaluationSubmitted(self._conf).getHTML()
    def _setActiveTab( self ):
        self._tabEvaluationPreview.setActive()



class WPConfModifEvaluationResults( WPConfModifEvaluationBase ):
    """[ManagementArea] Results of an Evaluation."""
    def _getTabContent( self, params ):
        sessionVarName = "selectedSubmissions_%s_%s" % (self._conf.getId(), self._conf.getEvaluation().getId())
        pars = {"selectedSubmissions": session.get(sessionVarName)}
        return WConfModifEvaluationResults(self._conf).getHTML(pars)
    def _setActiveTab( self ):
        self._tabEvaluationResults.setActive()

class WConfModifEvaluationResults( wcomponents.WTemplated ):
    """[ManagementArea] Results of an Evaluation."""
    def __init__( self, conference ):
        self._conf = conference
    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        evaluation = self._conf.getEvaluation()
        vars["evaluation"] = evaluation
        vars["Box"] = Box
        vars["Choice"] = Choice
        vars["actionUrl"] = urlHandlers.UHConfModifEvaluationResultsOptions.getURL(self._conf)
        vars["selectSubmitters"] = Evaluation._SELECT_SUBMITTERS
        vars["removeSubmitters"] = Evaluation._REMOVE_SUBMITTERS
        #submitters
        selectedSubmissions = evaluation.getSubmissions(vars["selectedSubmissions"])
        submitters = [sub.getSubmitterName() for sub in selectedSubmissions if isinstance(sub, Submission)]
        vars["submittersContext"] = "<br/> ".join(submitters)
        if not vars["selectedSubmissions"] and vars["selectedSubmissions"] is not None:
            vars["submittersVisible"] = _("NONE")
        elif len(submitters) >= evaluation.getNbOfSubmissions():
            vars["submittersVisible"] = _("ALL")
        elif len(submitters) > 3 :
            del submitters[3:]
            submitters.append("...")
            vars["submittersVisible"] = "; ".join(submitters).replace(", ", "&nbsp;")
        else:
            vars["submittersVisible"] = "; ".join(submitters).replace(", ", "&nbsp;")
        return vars


class WPConfModifEvaluationResultsSubmitters( WPConfModifEvaluationBase ):
    """[ManagementArea] Edition of submitters for the results."""
    def __init__( self, rh, conf, mode ):
        self._mode = mode
        WPConfModifEvaluationBase.__init__(self, rh, conf)
    def _getTabContent( self, params ):
        sessionVarName = "selectedSubmissions_%s_%s" % (self._conf.getId(), self._conf.getEvaluation().getId())
        pars = {"selectedSubmissions": session.get(sessionVarName)}
        return WConfModifEvaluationResultsSubmitters(self._conf, self._mode).getHTML(pars)
    def _setActiveTab( self ):
        self._tabEvaluationResults.setActive()

class WConfModifEvaluationResultsSubmitters( wcomponents.WTemplated ):
    """[ManagementArea] Edition of submitters for the results."""
    def __init__( self, conf, mode):
        self._conf = conf
        self._mode = mode
    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["mode"] = self._mode
        vars["isModeSelect"] = self._mode==Evaluation._SELECT_SUBMITTERS
        vars["submissions"] = self._conf.getEvaluation().getSubmissions()
        vars["utils"] = utils
        vars["actionUrl"] = urlHandlers.UHConfModifEvaluationResultsSubmittersActions.getURL(self._conf)
        if self._mode==Evaluation._REMOVE_SUBMITTERS :
            vars["inputCheckboxName"] = "removedSubmitters"
            vars["inputSubmitStyle"] = 'style="color:#ee0000"'
            vars["submitConfirm"] = """onsubmit="javascript:return confirmation();" """
        elif self._mode==Evaluation._SELECT_SUBMITTERS :
            vars["inputCheckboxName"] = "selectedSubmitters"
            vars["inputSubmitStyle"] = ''
            vars["submitConfirm"] = ''
        else:
            if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive(): raise Exception("Evaluation - unknown mode (given: %s)"%self._mode)
            vars["inputCheckboxName"] = "unknownMode"
            vars["inputSubmitStyle"] = ''
            vars["submitConfirm"] = ''
        return vars
