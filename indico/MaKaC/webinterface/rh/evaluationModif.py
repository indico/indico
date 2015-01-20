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
from cStringIO import StringIO
from flask import session

from MaKaC.webinterface       import urlHandlers
from MaKaC.webinterface.rh    import conferenceModif
from MaKaC.webinterface.pages import evaluations
from datetime                 import datetime
from MaKaC.evaluation         import Box,Choice,Textbox,Textarea,Password,Select,Radio,Checkbox
from MaKaC.evaluation         import Evaluation,Question,MultipleChoicesAnswer,TextAnswer
from MaKaC.common             import utils
from MaKaC.errors             import FormValuesError, MaKaCError
from MaKaC.export.excel       import ExcelGenerator
from xml.dom.minidom          import parseString,Element
from indico.core.config import Config
from MaKaC.i18n import _
from indico.web.flask.util import send_file


class RHEvaluationBase(conferenceModif.RHConferenceModifBase):
    """Basis of an Evaluation"""

    def _checkProtection(self):
        conferenceModif.RHConferenceModifBase._checkProtection(self)
        if not self._conf.hasEnabledSection("evaluation"):
            raise MaKaCError( _("The Evaluation form was disabled by the conference managers."), _("evaluation"))

class RHEvaluationSetup(RHEvaluationBase):
    """Modification of an Evaluation."""

    def _process(self):
        return evaluations.WPConfModifEvaluationSetup(self, self._conf).display()

class RHEvaluationSetupChangeStatus( RHEvaluationBase ):
    """changes status of an Evaluation."""

    def _checkParams( self, params ):
        RHEvaluationBase._checkParams( self, params )
        self._newStatus = params.get("changeTo", False)

    def _process( self ):
        evaluation = self._conf.getEvaluation()
        if self._newStatus == "True" :
            evaluation.setVisible(True)
        else:
            evaluation.setVisible(False)
        self._redirect(urlHandlers.UHConfModifEvaluationSetup.getURL(self._conf))

class RHEvaluationSetupSpecialAction( RHEvaluationBase ):
    """processes a special action."""

    def _process( self ):
        params = self.getRequestParams()
        evaluation = self._conf.getEvaluation()
        sessionVarName = "selectedSubmissions_%s_%s"%(self._conf.getId(), evaluation.getId())
        if 'exportXML' in params:
            return self._exportXml(evaluation, params)
        elif 'importXML' in params:
            return evaluations.WPConfModifEvaluationSetupImportXml( self, self._conf ).display()
        elif 'importedXML' in params:
            self._importedXml(evaluation, params)
        elif 'removeSubmissions' in params:
            session.pop(sessionVarName, None)
            evaluation.removeAllSubmissions()
        elif 'removeQuestions' in params:
            session.pop(sessionVarName, None)
            evaluation.removeAllQuestions()
        elif 'reinit' in params:
            session.pop(sessionVarName, None)
            evaluation.reinit()
        self._redirect(urlHandlers.UHConfModifEvaluationSetup.getURL(self._conf))

    def _exportXml(self, evaluation, params):
        """exportation of an evaluation."""
        from MaKaC.common.xmlGen import XMLGen
        xmlGen = XMLGen()
        evaluation.exportXml(xmlGen)
        return send_file(Evaluation._XML_FILENAME, StringIO(xmlGen.getXml()), 'XML', inline=False)

    def _importedXml(self, evaluation, params):
        """ Importation of an evaluation.
            Note: original 'isVisible' and the dates are kept.
        """
        try:
            xmlString = params["xmlFile"].file.read()
        except AttributeError: #no file given
            self._redirect(urlHandlers.UHConfModifEvaluationSetup.getURL(self._conf))
            return
        try:
            doc = parseString(xmlString)
        except:
            raise MaKaCError( _("""System can't import an evaluation from your file.
                                Be sure to import the right XML file."""), _("evaluation"))
        #parse begins
        evalNode = self._getElement(doc,"evaluation")
        if params.get("configOption","")=="imported":
            #parse node /evaluation/
            title                = self._getValue(evalNode,"title")
            announcement         = self._getValue(evalNode,"announcement")
            submissionsLimit     = self._getValue(evalNode,"submissionsLimit")
            contactInfo          = self._getValue(evalNode,"contactInfo")
            mandatoryAccount     = self._getValue(evalNode,"mandatoryAccount")
            mandatoryParticipant = self._getValue(evalNode,"mandatoryParticipant")
            anonymous            = self._getValue(evalNode,"anonymous")
            evaluation.setTitle(title)
            evaluation.setAnnouncement(announcement)
            evaluation.setSubmissionsLimit(submissionsLimit)
            evaluation.setContactInfo(contactInfo)
            evaluation.setMandatoryAccount(mandatoryAccount)
            evaluation.setMandatoryParticipant(mandatoryParticipant)
            if anonymous.strip()=="" :
                evaluation.setAnonymous(True)
            else :
                evaluation.setAnonymous(anonymous)
            #parse node /evaluation/notifications/
            notificationsNode    = self._getElement(evalNode, "notifications")
            evaluation.removeAllNotifications()
            for notificationNode in notificationsNode.childNodes :
                if isinstance(notificationNode, Element) :
                    from MaKaC.registration import Notification
                    notification = Notification()
                    toList       = self._getValue(notificationNode,"toList")
                    ccList       = self._getValue(notificationNode,"ccList")
                    notification.setToList( utils.getEmailList(toList) )
                    notification.setCCList( utils.getEmailList(ccList) )
                    evaluation.setNotification(notificationNode.tagName, notification)
        if params.get("questionsOption","")!="current" : # in ["imported", "both"]
            if params.get("questionsOption","")=="imported" :
                evaluation.removeAllQuestions()
            #parse node /evaluation/questions/
            questionsNode        = self._getElement(evalNode,"questions")
            for questionNode in questionsNode.childNodes :
                if isinstance(questionNode, Element):
                    questionValue= self._getValue(questionNode,"questionValue")
                    keyword      = self._getValue(questionNode,"keyword")
                    required     = self._getValue(questionNode,"required")
                    description  = self._getValue(questionNode,"description")
                    help         = self._getValue(questionNode,"help")
                    try:
                        question = eval(questionNode.tagName)()
                        if isinstance(question, Question):
                            question.setQuestionValue(questionValue)
                            question.setKeyword(keyword)
                            question.setRequired(required)
                            question.setDescription(description)
                            question.setHelp(help)
                            evaluation.insertQuestion(question)
                    except NameError:
                        raise MaKaCError( _("""xml parse error: unknown question type "%s"
                                            """)%questionNode.tagName, _("evaluation"))
                    if isinstance(question, Box):
                        defaultAnswer= self._getValue(questionNode,"defaultAnswer")
                        question.setDefaultAnswer(defaultAnswer)
                    elif isinstance(question, Choice):
                        #parse node /evaluation/questions/*/choiceItems/
                        choiceItemsNode = self._getElement(questionNode,"choiceItems")
                        for choiceItemNode in choiceItemsNode.childNodes :
                            if isinstance(choiceItemNode, Element):
                                itemText = self._getValue(choiceItemNode,"itemText")
                                if itemText.strip()!="" :
                                    isSelected = self._getValue(choiceItemNode,"isSelected")
                                    question.insertChoiceItem(itemText, isSelected)

    def _getElement(self, container, tagname):
        """ Find the first element with given tagname contained in given container element.
            If not found, return an empty Element tagged "_empty" (in order to avoid crashes).

            Params:
                container -- an Element containing the wanted element
                tagname -- tag (str) of the wanted element
        """
        if not hasattr(container, "getElementsByTagName"):
            return Element("_empty")
        #get a leaf node with given tagname contained within given node
        leafNodes = container.getElementsByTagName(tagname)
        if len(leafNodes)>0 :
            return leafNodes[0]
        else :
            return Element("_empty")

    def _getValue(self, container, tagname):
        """ finds the first leaf element with given tagname contained in given element,
            and returns its value.

            Params:
                container -- a non leaf Element containing the wanted leaf element
                tagname -- tag (str) of the wanted leaf element
        """
        if not hasattr(container, "getElementsByTagName"):
            return ""
        leafNode = self._getElement(container, tagname)
        #given a leaf node, returns its value.
        return utils.nodeValue(leafNode)

class RHEvaluationSetupDataModif( RHEvaluationBase ):
    """called when you want to change general parameters of your evaluation."""

    def _process( self ):
        return evaluations.WPConfModifEvaluationSetupDataModif( self, self._conf ).display()

class RHEvaluationSetupPerformDataModif( RHEvaluationBase ):
    """performs changes to general parameters of the evaluation."""

    def _process( self ):
        params = self.getRequestParams()
        if params.has_key("modify"):
            from MaKaC.registration import Notification
            evaluation = self._conf.getEvaluation()
            try:
                sDate = datetime( int( params["sYear"] ), \
                                  int( params["sMonth"] ), \
                                  int( params["sDay"] ) )
            except ValueError,e:
                raise FormValuesError("The start date you have entered is not correct: %s"%e, "Evaluation")
            try:
                eDate = datetime( int( params["eYear"] ), \
                                   int( params["eMonth"] ), \
                                   int( params["eDay"] ) )
            except ValueError,e:
                raise FormValuesError("The end date you have entered is not correct: %s"%e, "Evaluation")
            if eDate < sDate :
                raise FormValuesError("End date can't be before start date!", "Evaluation")
            evaluation.setStartDate(sDate)
            evaluation.setEndDate(eDate)
            evaluation.setAnonymous(params.has_key("anonymous"))
            evaluation.setAnnouncement(params.get("announcement",""))
            evaluation.setTitle( params.get("title","Evaluation") )
            evaluation.setContactInfo( params.get("contactInfo","") )
            evaluation.setMandatoryParticipant(params.has_key("mandatoryParticipant"))
            evaluation.setMandatoryAccount(params.has_key("mandatoryAccount"))
            try:
                evaluation.setSubmissionsLimit( params.get("submissionsLimit",0) )
            except ValueError,e:
                raise FormValuesError("You must enter an integer for 'Max number of submissions'!", "Evaluation")
            #notifications
            evaluationStartNotifyTo = utils.getEmailList(params.get("evaluationStartNotifyTo", ""))
            evaluationStartNotifyCc = utils.getEmailList(params.get("evaluationStartNotifyCc", ""))
            newSubmissionNotifyTo = utils.getEmailList(params.get("newSubmissionNotifyTo", ""))
            newSubmissionNotifyCc = utils.getEmailList(params.get("newSubmissionNotifyCc", ""))
            if params.has_key("notifyAllAdherents") :
                if self.getWebFactory()!=None : #Event == Meeting/Lecture
                    for participant in evaluation.getConference().getParticipation().getParticipantList() :
                        email = participant.getEmail()
                        if email not in evaluationStartNotifyTo :
                            evaluationStartNotifyTo.append(email)
                else : #Event == Conference
                    for registrant in evaluation.getConference().getRegistrantsList() :
                        email = registrant.getEmail()
                        if email not in evaluationStartNotifyTo :
                            evaluationStartNotifyTo.append(email)
            if len( evaluationStartNotifyTo + evaluationStartNotifyCc ) < 1 :
                evaluation.removeNotification(Evaluation._EVALUATION_START)
            else :
                evaluationStartNotification = Notification()
                evaluationStartNotification.setToList(evaluationStartNotifyTo)
                evaluationStartNotification.setCCList(evaluationStartNotifyCc)
                evaluation.setNotification(Evaluation._EVALUATION_START, evaluationStartNotification)
            if len( newSubmissionNotifyTo + newSubmissionNotifyCc ) < 1 :
                evaluation.removeNotification(Evaluation._NEW_SUBMISSION)
            else :
                newSubmissionNotification   = Notification()
                newSubmissionNotification.setToList(newSubmissionNotifyTo)
                newSubmissionNotification.setCCList(newSubmissionNotifyCc)
                evaluation.setNotification(Evaluation._NEW_SUBMISSION, newSubmissionNotification)

        #redirecting...
        self._redirect(urlHandlers.UHConfModifEvaluationSetup.getURL(self._conf))


class RHEvaluationEdit(RHEvaluationBase):
    """Edition of questions of an Evaluation."""

    def _process(self):
        return evaluations.WPConfModifEvaluationEdit(self, self._conf).display()

class RHEvaluationEditPerformChanges( RHEvaluationBase ):
    """performs changes for Evaluation questions."""

    def _process( self ):
        ####################
        #get some variables#
        ####################
        self._evaluation = self._conf.getEvaluation()
        params = self.getRequestParams()
        save = params.has_key("save")
        type = params.get("type", "")
        mode = params.get("mode","")
        questionValue = params.get("questionValue","").strip()
        keyword = params.get("keyword","").strip()

        ###################
        #check consistency#
        ###################
        if save:
            if questionValue=="" or keyword=="":
                raise FormValuesError("Please enter question and keyword!", "Evaluation")
            if type in Question._CHOICE_SUBTYPES :
                choiceItem_1 = params.get("choiceItem_1","").strip()
                choiceItem_2 = params.get("choiceItem_2","").strip()
                if choiceItem_1=="" or choiceItem_2=="":
                    raise FormValuesError("Please enter all values for Choice Items.", "Evaluation")
                if choiceItem_1==choiceItem_2:
                    raise FormValuesError("Please enter different values for Choice Items.", "Evaluation")

        ##########
        #Add mode#
        ##########
        if mode==Question._ADD and save:
            #create new Question depending on the type selected...
            if   type == Question._TEXTBOX:  question = Textbox()
            elif type == Question._TEXTAREA: question = Textarea()
            elif type == Question._PASSWORD: question = Password()
            elif type == Question._SELECT:   question = Select()
            elif type == Question._RADIO:    question = Radio()
            elif type == Question._CHECKBOX: question = Checkbox()
            else:
                raise FormValuesError("unknown question type!", "Evaluation")
            #set params for question
            self._setQuestionParams(question, params)

        ###########
        #Edit mode#
        ###########
        elif mode==Question._EDIT:
            #the user edited a question.
            if save:
                #DON'T USE params:newPos BUT params:questionPos which is edited question position!!!
                question = self._evaluation.getQuestionAt(params.get("questionPos",-1))
                if question == None:
                    raise FormValuesError("No question found at the given position!", "Evaluation")
                else:
                    #set params for question
                    self._setQuestionParams(question, params)
            #look if the user requested to change the position of a question.
            else:
                questions_nb = self._evaluation.getNbOfQuestions()
                for i in range(1, questions_nb+1):
                    posChange = int(params.get("posChange_"+str(i), -1))
                    if posChange>0:
                        self._evaluation.getQuestionAt(i).setPosition(posChange)

        #############
        #Delete mode#
        #############
        elif mode==Question._REMOVE:
            #DON'T USE params:newPos BUT params:questionPos which is edited question position!!!
            self._evaluation.removeQuestion(int(params.get("questionPos",-1)))

        #redirecting...
        self._redirect(urlHandlers.UHConfModifEvaluationEdit.getURL(self._conf))

    def _setQuestionParams(self, question, params):
        """ set the parameters for the given question with the dictionary (params).
            Params:
                question -- question to be edited.
                params -- dictionary of parameters.
        """
        #check
        if not isinstance(question, Question) or not isinstance(params, dict): return
        #setting the attributes for the Question...
        question.setQuestionValue(params.get("questionValue",""))
        question.setKeyword(params.get("keyword",""))
        question.setRequired(params.has_key("required"))
        question.setDescription(params.get("description",""))
        question.setHelp(params.get("help",""))
#        question.setLevel(params.get("level",1))
        #position
        newPos = int(params.get("newPos",-1))
        #[ADD] When no evaluation for this question: add question in the evaluation.
        if question.getEvaluation()==None:
            #USE params:newPos for setting the new posision.
            self._evaluation.insertQuestion(question, newPos)
        #[EDIT] When this question is linked to an evaluation: set its position.
        else:
            question.setPosition(newPos)
        #default answer
        if isinstance(question, Box):
            question.setDefaultAnswer(params.get("defaultAnswer",""))
        #choice items
        elif isinstance(question, Choice):
            selectedChoiceItems = params.get("selectedChoiceItems",[])
            #reinit choice items if already exists.
            question.removeAllChoiceItems()
            #init variables for while loop
            currentItemId = 1
            itemText = ""
            while itemText != None:
                itemText = params.get( "choiceItem_"+str(currentItemId) , None )
                #If text has been well filled in, add it. Otherwise do nothing (i.e. don't add it).
                if itemText!=None and itemText.strip()!="" :
                    isSelected = str(currentItemId) in selectedChoiceItems
                    question.insertChoiceItem(itemText, isSelected)
                currentItemId += 1


class RHEvaluationPreview(RHEvaluationBase):
    """Preview of an Evaluation."""

    def _process(self):
        params = self.getRequestParams()
        if params.get("status","")==_("submitted") and params.has_key("submit"):
            return evaluations.WPConfModifEvaluationPreviewSubmitted(self, self._conf).display()
        else:
            return evaluations.WPConfModifEvaluationPreview(self, self._conf).display()


class RHEvaluationResults(RHEvaluationBase):
    """Results of an Evaluation."""

    def _process(self):
        return evaluations.WPConfModifEvaluationResults(self, self._conf).display()


class RHEvaluationResultsOptions(RHEvaluationBase):
    """Do asked actions for the results."""

    def _process(self):
        ####################
        #get some variables#
        ####################
        evaluation = self._conf.getEvaluation()
        params = self.getRequestParams()
        export = params.has_key("exportStats")
        select = params.has_key(Evaluation._SELECT_SUBMITTERS)
        remove = params.has_key(Evaluation._REMOVE_SUBMITTERS)

        ##############
        #export stats# (CSV)
        ##############
        if export:
            excelGen = ExcelGenerator()
            #csv: header
            excelGen.addValue("Pseudonym")
            excelGen.addValue("submissionDate")
            excelGen.addValue("modificationDate")
            for question in evaluation.getQuestions() :
                excelGen.addValue(question.getKeyword())
                #fill blank cells for the choice items if there are.
                if question.getAnswerClass()==MultipleChoicesAnswer :
                    #above: only Checkbox is concerned but this way it's more generic.
                    for i in range(1, question.getNbOfChoiceItems()) :
                        excelGen.addValue("---")
            excelGen.newLine()
            #csv: data
            for submission in evaluation.getSubmissions() :
                excelGen.newLine()
                excelGen.addValue(submission.getSubmitterName())
                excelGen.addValue(submission.getSubmissionDate(str))
                excelGen.addValue(submission.getModificationDate(str))
                for question in evaluation.getQuestions() :
                    answer = submission.getDictQuestionsAnswers().get(question,None)
                    if question.getAnswerClass()==TextAnswer :
                        if answer==None :
                            excelGen.addValue("")
                        else:
                            excelGen.addValue(utils.putbackQuotes(answer.getAnswerValue()))
                    elif question.getAnswerClass()==MultipleChoicesAnswer :
                        if answer==None :
                            for i in range(0, question.getNbOfChoiceItems()) :
                                excelGen.addValue("")
                        else:
                            for ci in question.getChoiceItemsOrderedKeys() :
                                if ci in answer.getAnswerValue() :
                                    excelGen.addValue(utils.putbackQuotes(ci))
                                else :
                                    excelGen.addValue("")
            return send_file(Evaluation._CSV_FILENAME, StringIO(excelGen.getExcelContent()), 'CSV')

        ########
        #remove#
        ########
        elif remove:
            return evaluations.WPConfModifEvaluationResultsSubmitters(
                                   self, self._conf, Evaluation._REMOVE_SUBMITTERS).display()
        ########
        #select#
        ########
        elif select:
            return evaluations.WPConfModifEvaluationResultsSubmitters(
                                   self, self._conf, Evaluation._SELECT_SUBMITTERS).display()
        #redirecting...
        self._redirect(urlHandlers.UHConfModifEvaluationResults.getURL(self._conf))

class RHEvaluationResultsSubmittersActions(RHEvaluationBase):
    """Do asked actions for the submitters."""

    def _process(self):
        ####################
        #get some variables#
        ####################
        evaluation = self._conf.getEvaluation()
        params = self.getRequestParams()
        remove = params.has_key(Evaluation._REMOVE_SUBMITTERS)
        select = params.has_key(Evaluation._SELECT_SUBMITTERS)
        sessionVarName = "selectedSubmissions_%s_%s"%(self._conf.getId(), evaluation.getId())

        ########
        #remove#
        ########
        if remove:
            removedSubmitters = set(params.get("removedSubmitters", []))
            if removedSubmitters:
                #remove submissions in session variable
                if sessionVarName in session:
                    selectedSubmissions = session.setdefault(sessionVarName, set())
                    selectedSubmissions -= removedSubmitters
                    session.modified = True
                #remove submissions in database
                removedSubmissions = set(s for s in evaluation.getSubmissions() if s.getId() in removedSubmitters)
                for submission in removedSubmissions:
                    evaluation.removeSubmission(submission)

        ##########
        #selected#
        ##########
        elif select:
            selectedSubmitters = params.get("selectedSubmitters", [])
            if isinstance(selectedSubmitters, str):
                selectedSubmitters = [selectedSubmitters]
            #insert selected submissions list in a session variable
            selected = set(s.getId() for s in evaluation.getSubmissions() if s.getId() in selectedSubmitters)
            if len(selected) != len(evaluation.getSubmissions()):
                session[sessionVarName] = selected
            else:
                # Everything selected => DELETE session var since that means "everything" and will stay that way when
                # a new evaluation is submitted.
                session.pop(sessionVarName, None)

        #redirecting...
        self._redirect(urlHandlers.UHConfModifEvaluationResults.getURL(self._conf))
