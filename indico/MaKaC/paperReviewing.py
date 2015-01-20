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

from MaKaC.common import log
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import urlHandlers
from MaKaC.common.mail import GenericMailer
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc
from datetime import datetime
from persistent import Persistent
from MaKaC.errors import MaKaCError
import tempfile
from indico.core.config import Config
import conference
from MaKaC.common.Counter import Counter
from MaKaC.fossils.reviewing import IReviewingQuestionFossil, IReviewingStatusFossil
from MaKaC.common.fossilize import fossilizes, Fossilizable
from persistent.list import PersistentList
from MaKaC.i18n import _

###############################################
# Conference-wide classes
###############################################


class ConferencePaperReview(Persistent):
    """
    This class manages the parameters of the paper reviewing.
    """
    reviewingModes = ["", "No reviewing", "Content reviewing", "Layout reviewing", "Content and layout reviewing"]
    predefinedStates = ["Accept", "To be corrected", "Reject"]
    reviewingQuestionsAnswers = ["Strongly Disagree", "Disagree", "Weakly Disagree", "Borderline", "Weakly Agree", "Agree", "Strongly Agree"]
    reviewingQuestionsLabels = ["-3", "", "", "0", "", "", "+3"]
    initialSelectedAnswer = 3
    # Reviewing constant values
    NO_REVIEWING = 1
    CONTENT_REVIEWING = 2
    LAYOUT_REVIEWING = 3
    CONTENT_AND_LAYOUT_REVIEWING = 4

    def __init__( self, conference):
        """ Constructor.
            conference must be a Conference object (not an id).
        """

        self._conference = conference

        #lists of users with reviewing roles
        self._reviewersList = []
        self._editorsList = []
        self._refereesList = []
        self._paperReviewManagersList = []

        self._refereeContribution = {} #key: user, value: list of contributions where user is referee
        self._editorContribution = {} #key: user, value: list of contributions where user is editor
        self._reviewerContribution = {} #key: user, value: list of contributions where user is reviewer

        self.setChoice(self.NO_REVIEWING) #initial reviewing mode: no reviewing

        #default dates
        self._startSubmissionDate = None
        self._endSubmissionDate = None
        self._defaultRefereeDueDate = None
        self._defaultEditorDueDate = None
        self._defaultReviwerDueDate = None

        #auto e-mails
        self._enablePRMEmailNotif = True
        self._enableRefereeEmailNotif = False
        self._enableEditorEmailNotif = False
        self._enableReviewerEmailNotif = False
        self._enableRefereeEmailNotifForContribution = False
        self._enableEditorEmailNotifForContribution = False
        self._enableReviewerEmailNotifForContribution = False
        self._enableRefereeJudgementEmailNotif = False
        self._enableEditorJudgementEmailNotif = False
        self._enableReviewerJudgementEmailNotif = False
        self._enableAuthorSubmittedMatRefereeEmailNotif = False
        self._enableAuthorSubmittedMatEditorEmailNotif = False
        self._enableAuthorSubmittedMatReviewerEmailNotif = False
        self._enableEditorSubmittedRefereeEmailNotif = False
        self._enableReviewerSubmittedRefereeEmailNotif = False

        self._statuses = [] # list of content reviewing and final judgement
        self._reviewingQuestions = [] #list of content reviewing and final judgement questions
        self._layoutQuestions = [] #list of layout editing criteria
        self._templates = {} #dictionary with layout templates. key: id, value: Template object
        self._templateCounter = Counter(1) #counter to make new id's for the templates
        self._userCompetences = {} #dictionary with the competences of each user. key: user, value: list of competences
        self._userCompetencesByTag = {} #dictionary with the users for each competence. key: competence, value: list of users
        self._reviewingMaterials = {}
        self.notifyModification()

        # id generators
        self._statusCounter = Counter(1)
        self._questionCounter = Counter(1)
        self._answerCounter = Counter(1)
        self.addStatus("Accept", False)
        self.addStatus("To be corrected", False)
        self.addStatus("Reject", False)


    def getConference(self):
        """ Returns the parent conference of the ConferencePaperReview object
        """
        return self._conference

    def setStartSubmissionDate(self, startSubmissionDate):
        self._startSubmissionDate= datetime(startSubmissionDate.year,startSubmissionDate.month,startSubmissionDate.day,23,59,59)

    def getStartSubmissionDate(self):
        return self._startSubmissionDate

    def setEndSubmissionDate(self, endSubmissionDate):
        self._endSubmissionDate = datetime(endSubmissionDate.year,endSubmissionDate.month,endSubmissionDate.day,23,59,59)

    def getEndSubmissionDate(self):
        return self._endSubmissionDate

    def setDefaultRefereeDueDate(self, date):
        self._defaultRefereeDueDate = date

    def getDefaultRefereeDueDate(self):
        return self._defaultRefereeDueDate

    def getAdjustedDefaultRefereeDueDate(self):
        if self.getDefaultRefereeDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._defaultRefereeDueDate, self.getConference())

    def setDefaultEditorDueDate(self, date):
        self._defaultEditorDueDate = date

    def getDefaultEditorDueDate(self):
        return self._defaultEditorDueDate

    def getAdjustedDefaultEditorDueDate(self):
        if self.getDefaultEditorDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._defaultEditorDueDate, self.getConference())

    def setDefaultReviewerDueDate(self, date):
        self._defaultReviwerDueDate = date

    def getDefaultReviewerDueDate(self):
        return self._defaultReviwerDueDate

    def getAdjustedDefaultReviewerDueDate(self):
        if self.getDefaultReviewerDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._defaultReviwerDueDate, self.getConference())

    #auto e-mails methods for assign/remove reviewing team to the conference notification
    def getEnablePRMEmailNotif(self):
        return self._enablePRMEmailNotif

    def enablePRMEmailNotif(self):
        self._enablePRMEmailNotif = True

    def disablePRMEmailNotif(self):
        self._enablePRMEmailNotif = False

    def getEnableRefereeEmailNotif(self):
        return self._enableRefereeEmailNotif

    def enableRefereeEmailNotif(self):
        self._enableRefereeEmailNotif = True

    def disableRefereeEmailNotif(self):
        self._enableRefereeEmailNotif = False


    def getEnableEditorEmailNotif(self):
        return self._enableEditorEmailNotif

    def enableEditorEmailNotif(self):
        self._enableEditorEmailNotif = True

    def disableEditorEmailNotif(self):
        self._enableEditorEmailNotif = False


    def getEnableReviewerEmailNotif(self):
        return self._enableReviewerEmailNotif

    def enableReviewerEmailNotif(self):
        self._enableReviewerEmailNotif = True

    def disableReviewerEmailNotif(self):
        self._enableReviewerEmailNotif = False


    #auto e-mails methods for assign/remove reviewers to/from contributions notification
    def getEnableRefereeEmailNotifForContribution(self):
        return self._enableRefereeEmailNotifForContribution

    def enableRefereeEmailNotifForContribution(self):
        self._enableRefereeEmailNotifForContribution = True

    def disableRefereeEmailNotifForContribution(self):
        self._enableRefereeEmailNotifForContribution = False

    def getEnableEditorEmailNotifForContribution(self):
        return self._enableEditorEmailNotifForContribution

    def enableEditorEmailNotifForContribution(self):
        self._enableEditorEmailNotifForContribution = True

    def disableEditorEmailNotifForContribution(self):
        self._enableEditorEmailNotifForContribution = False

    def getEnableReviewerEmailNotifForContribution(self):
        return self._enableReviewerEmailNotifForContribution

    def enableReviewerEmailNotifForContribution(self):
        self._enableReviewerEmailNotifForContribution = True

    def disableReviewerEmailNotifForContribution(self):
        self._enableReviewerEmailNotifForContribution = False

    #auto e-mails methods for reviewers judgements notification
    def getEnableRefereeJudgementEmailNotif(self):
        return self._enableRefereeJudgementEmailNotif

    def enableRefereeJudgementEmailNotif(self):
        self._enableRefereeJudgementEmailNotif = True

    def disableRefereeJudgementEmailNotif(self):
        self._enableRefereeJudgementEmailNotif = False

    def getEnableEditorJudgementEmailNotif(self):
        return self._enableEditorJudgementEmailNotif

    def enableEditorJudgementEmailNotif(self):
        self._enableEditorJudgementEmailNotif = True

    def disableEditorJudgementEmailNotif(self):
        self._enableEditorJudgementEmailNotif = False

    def getEnableReviewerJudgementEmailNotif(self):
        return self._enableReviewerJudgementEmailNotif

    def enableReviewerJudgementEmailNotif(self):
        self._enableReviewerJudgementEmailNotif = True

    def disableReviewerJudgementEmailNotif(self):
        self._enableReviewerJudgementEmailNotif = False

    def getEnableEditorSubmittedRefereeEmailNotif(self):
        if not hasattr(self, "_enableEditorSubmittedRefereeEmailNotif"):
            self._enableEditorSubmittedRefereeEmailNotif = False
        return self._enableEditorSubmittedRefereeEmailNotif

    def enableEditorSubmittedRefereeEmailNotif(self):
        self._enableEditorSubmittedRefereeEmailNotif = True

    def disableEditorSubmittedRefereeEmailNotif(self):
        self._enableEditorSubmittedRefereeEmailNotif = False

    def getEnableReviewerSubmittedRefereeEmailNotif(self):
        if not hasattr(self, "_enableReviewerSubmittedRefereeEmailNotif"):
            self._enableReviewerSubmittedRefereeEmailNotif = False
        return self._enableReviewerSubmittedRefereeEmailNotif

    def enableReviewerSubmittedRefereeEmailNotif(self):
        self._enableReviewerSubmittedRefereeEmailNotif = True

    def disableReviewerSubmittedRefereeEmailNotif(self):
        self._enableReviewerSubmittedRefereeEmailNotif = False

    #auto e-mails methods for authors' submittion materials notification
    def getEnableAuthorSubmittedMatRefereeEmailNotif(self):
        return self._enableAuthorSubmittedMatRefereeEmailNotif

    def enableAuthorSubmittedMatRefereeEmailNotif(self):
        self._enableAuthorSubmittedMatRefereeEmailNotif = True

    def disableAuthorSubmittedMatRefereeEmailNotif(self):
        self._enableAuthorSubmittedMatRefereeEmailNotif = False

    def getEnableAuthorSubmittedMatEditorEmailNotif(self):
        return self._enableAuthorSubmittedMatEditorEmailNotif

    def enableAuthorSubmittedMatEditorEmailNotif(self):
        self._enableAuthorSubmittedMatEditorEmailNotif = True

    def disableAuthorSubmittedMatEditorEmailNotif(self):
        self._enableAuthorSubmittedMatEditorEmailNotif = False

    def getEnableAuthorSubmittedMatReviewerEmailNotif(self):
        return self._enableAuthorSubmittedMatReviewerEmailNotif

    def enableAuthorSubmittedMatReviewerEmailNotif(self):
        self._enableAuthorSubmittedMatReviewerEmailNotif = True

    def disableAuthorSubmittedMatReviewerEmailNotif(self):
        self._enableAuthorSubmittedMatReviewerEmailNotif = False

    #Reviewing mode methods
    def setChoice(self, choice):
        """ Sets the reviewing mode for the conference, as a number and as a string
            1: "No reviewing"
            2: "Content reviewing"
            3: "Layout reviewing"
            4: "Content and layout reviewing"
        """
        self._choice = choice
        self._reviewing = ConferencePaperReview.reviewingModes[choice]

    def getChoice(self):
        """ Returns the reviewing mode for the conference, as a number
            1: "No reviewing"
            2: "Content reviewing"
            3: "Layout reviewing"
            4: "Content and layout reviewing"
        """
        return self._choice

    def getReviewingMode(self):
        """ Returns the reviewing mode for the conference, as a string
        """
        return self._reviewing

    def setReviewingMode(self, mode):
        """ Sets the reviewing mode of the conference, as a string.
            The string has to be one of those in ConferencePaperReview.reviewingModes
        """
        if mode in ConferencePaperReview.reviewingModes:
            self._reviewing = mode
            self._choice = ConferencePaperReview.reviewingModes.index(mode)

    def hasReviewing(self):
        """ Convenience method that returns if the Conference has a reviewing mode active or not.
        """
        return self._choice > 1

    def hasPaperReviewing(self):
        """ Convenience method that returns if the Conference has a reviewing mode that allows paper reviewing.
            (modes 2 and 4)
        """
        return self._choice == self.CONTENT_REVIEWING or self._choice == self.CONTENT_AND_LAYOUT_REVIEWING

    def hasPaperEditing(self):
        """ Convenience method that returns if the Conference has a reviewing mode that allows paper editing.
            (modes 3 and 4)
        """
        return self._choice == self.LAYOUT_REVIEWING or self._choice == self.CONTENT_AND_LAYOUT_REVIEWING

    def inModificationPeriod(self):
        date = nowutc()
        if date <= self._endCorrectionDate:
            return True
        else:
            return False

    def inSubmissionPeriod(self):
        date = nowutc()
        if date <= self._endSubmissionDate & date >= self._startSubmissionDate:
            return True
        else:
            return False

    def inEditingPeriod(self):
        date = nowutc()
        if date <= self._endEditingDate:
            return True
        else:
            return False

    def inReviewingPeriod(self):
        date = nowutc()
        if date <= self._endReviewingDate & date >= self._endCorrectionDate:
            return True
        else:
            return False

    # Configurable options (for the future)
    def getNumberOfAnswers(self):
        """ Returns the number of possible answers (radio buttons) per question
        """
        return len(ConferencePaperReview.reviewingQuestionsLabels)


    # status methods
    def addStatus(self, name, editable):
        """ Adds this status at the end of the list of statuses list
        """
        newId = self.getNewStatusId()
        status = Status(newId,name,editable)
        self._statuses.append(status)
        self.notifyModification()

    def getStatusById(self, statusId):
        """ Return the status with the especified id """
        for status in self._statuses:
            if (statusId == status.getId()):
                return status

    def getStatuses(self):
        """ Returns the list of statuses
        """
        # Filter the non editable statuses
        editableStatuses = []
        for status in self._statuses:
            if status.getEditable():
                editableStatuses.append(status)
        return editableStatuses

    def getDefaultStatusesDictionary(self):
        """ Returns a dictionary with the default statuses {id:name, ...}
        """
        dic = {}
        for status in self._statuses:
            # 1: Accept, 2: To be corrected, 3: Reject
            if ((status.getId() == "1") or (status.getId() == "2") or (status.getId() == "3")):
                dic[status.getId()] = status.getName()
        return dic


    def getStatusesDictionary(self):
        """ Returns a dictionary with the names of the statuses and the ids
        """
        dic = {}
        for status in self._statuses:
            dic[status.getId()] = status.getName()
        return dic

    def removeStatus(self, statusId):
        """ Removes a status from the list
        """
        status = self.getStatusById(statusId)

        if status:
            self._statuses.remove(status)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot remove a status which doesn't exist")

    def editStatus(self, statusId, newName):
        """ Edit the name of a status
        """
        status = self.getStatusById(statusId)

        if status:
            status.setName(newName)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot edit a question which doesn't exist")


    def getNewStatusId(self):
        """ Returns a new an unused questionId
            Increments the questionId counter
        """
        return self._statusCounter.newCount()


    # content reviewing and final judgement questions methods
    def addReviewingQuestion(self, text):
        """ Adds this question at the end of the list of questions
        """
        newId = self.getNewQuestionId()
        question = Question(newId,text)
        self._reviewingQuestions.append(question)
        self.notifyModification()

    def getReviewingQuestionById(self, questionId):
        """ Return the question with the especified id """
        for question in self._reviewingQuestions:
            if (questionId == question.getId()):
                return question

    def getReviewingQuestions(self):
        """ Returns the list of questions
        """
        return self._reviewingQuestions

    def removeReviewingQuestion(self, questionId):
        """ Removes a question from the list
        """
        question = self.getReviewingQuestionById(questionId)

        if question:
            self._reviewingQuestions.remove(question)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot remove a question which doesn't exist")

    def editReviewingQuestion(self, questionId, text):
        """ Edit the text of a question
        """
        question = self.getReviewingQuestionById(questionId)

        if question:
            question.setText(text)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot edit a question which doesn't exist")


    # layout editing criteria methods
    def addLayoutQuestion(self, text):
        """ Add a new layout editing criterion
        """
        newId = self.getNewQuestionId()
        question = Question(newId,text)
        self._layoutQuestions.append(question)
        self.notifyModification()

    def getLayoutQuestionById(self, questionId):
        """ Return the question with the especified id """
        for question in self._layoutQuestions:
            if (questionId == question.getId()):
                return question

    def getLayoutQuestions(self):
        """ Get the list of all the layout criteria
        """
        return self._layoutQuestions

    def removeLayoutQuestion(self, questionId):
        """ Remove one the layout question
        """
        question = self.getLayoutQuestionById(questionId)

        if question:
            self._layoutQuestions.remove(question)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot remove a question which doesn't exist")

    def editLayoutQuestion(self, questionId, text):
        """ Edit the text of a question
        """
        question = self.getLayoutQuestionById(questionId)

        if question:
            question.setText(text)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot edit a question which doesn't exist")

    def getNewQuestionId(self):
        """ Returns a new an unused questionId
            Increments the questionId counter
        """
        return self._questionCounter.newCount()

    #referee methods
    def addReferee(self, newReferee):
        """ Adds a new referee to the conference.
            newReferee has to be an Avatar object.
            The referee is sent a mail notification only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        if newReferee in self.getRefereesList():
            raise MaKaCError("This referee has already been added to this conference")
        else:
            self._refereesList.append(newReferee)
            newReferee.linkTo(self._conference, "referee")
            if not self._userCompetences.has_key(newReferee):
                self._userCompetences[newReferee] = []
            self.notifyModification()
            if self._enableRefereeEmailNotif == True:
                notification = ConferenceReviewingNotification(newReferee, 'Referee', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)


    def removeReferee(self, referee):
        """ Remove a referee from the conference.
            referee has to be an Avatar object.
            The referee is sent a mail notification only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        if referee in self._refereesList:
            if self._userCompetences.has_key(referee):
                if not ((referee in self._editorsList) or \
                        (referee in self._paperReviewManagersList) or \
                        (referee in self._reviewersList)):
                    self.clearUserCompetences(referee)
                    del(self._userCompetences[referee])
            self._refereesList.remove(referee)
            referee.unlinkTo(self._conference, "referee")
            self.notifyModification()
            if self._enableRefereeEmailNotif == True:
                notification = ConferenceReviewingRemoveNotification(referee, 'Referee', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)
        else:
            raise MaKaCError("Cannot remove a referee who is not yet referee")

    def isReferee(self, user):
        """ Returns if a given user is referee of the conference.
            user has to be an Avatar object.
        """
        return user in self._refereesList

    def getRefereesList(self):
        """ Returns the list of referees as a list of Avatar objects.
        """
        return self._refereesList

    def addRefereeContribution(self, referee, contribution):
        """ Adds the contribution to the list of contributions for a given referee.
            referee has to be an Avatar object.
        """
        if self._refereeContribution.has_key(referee):
            self._refereeContribution[referee].append(contribution)
            self._refereeContribution[referee].sort(key= lambda c: int(c.getId()))
        else:
            self._refereeContribution[referee] = [contribution]
        self.notifyModification()

    def removeRefereeContribution(self, referee, contribution):
        """ Removes the contribution from the list of contributions of this referee
            referee has to be an Avatar object.
        """
        if self._refereeContribution.has_key(referee):
            self._refereeContribution[referee].remove(contribution)
        self.notifyModification()

    def isRefereeContribution(self, referee, contribution):
        """ Returns if a user is referee for a given contribution
            referee has to be an Avatar object.
        """
        return self._refereeContribution.has_key(referee) and contribution in self._refereeContribution[referee]

    def getJudgedContributions(self, referee):
        """ Returns the list of contributions for a given referee
            referee has to be an Avatar object.
        """
        if self._refereeContribution.has_key(referee):
            return self._refereeContribution[referee]
        else:
            return []

    #editor methods
    def addEditor(self, newEditor):
        """ Adds a new editor to the conference.
            editor has to be an Avatar object.
            The editor is sent a mail notification only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        if newEditor in self.getEditorsList():
            raise MaKaCError("This editor has already been added to this conference")
        else:
            self._editorsList.append(newEditor)
            newEditor.linkTo(self._conference, "editor")
            if not self._userCompetences.has_key(newEditor):
                self._userCompetences[newEditor] = []
            self.notifyModification()
            if self._enableEditorEmailNotif == True:
                notification = ConferenceReviewingNotification(newEditor, 'Layout Reviewer', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)

    def removeEditor(self, editor):
        """ Remove a editor from the conference.
            editor has to be an Avatar object.
            The editor is sent a mail notification only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        if editor in self._editorsList:
            if self._userCompetences.has_key(editor):
                if not ((editor in self._paperReviewManagersList) or \
                        (editor in self._reviewersList) or \
                        (editor in self._refereesList)):
                    self.clearUserCompetences(editor)
                    del(self._userCompetences[editor])
            self._editorsList.remove(editor)
            editor.unlinkTo(self._conference, "editor")
            self.notifyModification()
            if self._enableEditorEmailNotif == True:
                notification = ConferenceReviewingRemoveNotification(editor, 'Layout Reviewer', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)
        else:
            raise MaKaCError("Cannot remove an editor who is not yet editor")

    def isEditor(self, user):
        """ Returns if a given user is editor of the conference.
            user has to be an Avatar object.
        """
        return user in self._editorsList

    def getEditorsList(self):
        """ Returns the list of editors as a list of users.
        """
        return self._editorsList

    def addEditorContribution(self, editor, contribution):
        """ Adds the contribution to the list of contributions for a given editor.
            editor has to be an Avatar object.
        """
        if self._editorContribution.has_key(editor):
            self._editorContribution[editor].append(contribution)
            self._editorContribution[editor].sort(key= lambda c: int(c.getId()))
        else:
            self._editorContribution[editor] = [contribution]
        self.notifyModification()

    def removeEditorContribution(self, editor, contribution):
        """ Removes the contribution from the list of contributions of this editor
            editor has to be an Avatar object.
        """
        if self._editorContribution.has_key(editor):
            self._editorContribution[editor].remove(contribution)
        self.notifyModification()

    def isEditorContribution(self, editor, contribution):
        """ Returns if a user is editor for a given contribution
            editor has to be an Avatar object.
        """
        return self._editorContribution.has_key(editor) and contribution in self._editorContribution[editor]

    def getEditedContributions(self, editor):
        """ Returns the list of contributions for a given editor
            editor has to be an Avatar object.
        """
        if self._editorContribution.has_key(editor):
            return self._editorContribution[editor]
        else:
            return []

    #reviewer methods
    def addReviewer(self, newReviewer):
        """ Adds a new reviewer to the conference.
            newreviewer has to be an Avatar object.
            The reviewer is sent a mail notification only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        if newReviewer in self.getReviewersList():
            raise MaKaCError("This reviewer has already been added to this conference")
        else:
            self._reviewersList.append(newReviewer)
            newReviewer.linkTo(self._conference, "reviewer")
            if not self._userCompetences.has_key(newReviewer):
                self._userCompetences[newReviewer] = []
            self.notifyModification()
            if self._enableReviewerEmailNotif == True:
                notification = ConferenceReviewingNotification(newReviewer, 'Content Reviewer', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)

    def removeReviewer(self, reviewer):
        """ Remove a reviewer from the conference.
            reviewer has to be an Avatar object.
            The reviewer is sent a mail notification only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        if reviewer in self._reviewersList:
            if self._userCompetences.has_key(reviewer):
                if not ((reviewer in self._editorsList) or \
                        (reviewer in self._paperReviewManagersList) or \
                        (reviewer in self._refereesList)):
                    self.clearUserCompetences(reviewer)
                    del(self._userCompetences[reviewer])
            self._reviewersList.remove(reviewer)
            reviewer.unlinkTo(self._conference, "reviewer")
            self.notifyModification()
            if self._enableReviewerEmailNotif == True:
                notification = ConferenceReviewingRemoveNotification(reviewer, 'Content Reviewer', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)
        else:
            raise MaKaCError("Cannot remove a reviewer who is not yet reviewer")

    def isReviewer(self, user):
        """ Returns if a given user is reviewer of the conference.
            user has to be an Avatar object.
        """
        return user in self._reviewersList

    def getReviewersList(self):
        """ Returns the list of reviewers as a list of users.
        """
        return self._reviewersList

    def addReviewerContribution(self, reviewer, contribution):
        """ Adds the contribution to the list of contributions for a given reviewer.
            reviewer has to be an Avatar object.
        """
        if self._reviewerContribution.has_key(reviewer):
            self._reviewerContribution[reviewer].append(contribution)
            self._reviewerContribution[reviewer].sort(key= lambda c: int(c.getId()))
        else:
            self._reviewerContribution[reviewer] = [contribution]
        self.notifyModification()

    def removeReviewerContribution(self, reviewer, contribution):
        """ Removes the contribution from the list of contributions of this reviewer
            reviewer has to be an Avatar object.
        """
        if self._reviewerContribution.has_key(reviewer):
            self._reviewerContribution[reviewer].remove(contribution)
        self.notifyModification()

    def isReviewerContribution(self, reviewer, contribution):
        """ Returns if a user is reviewer for a given contribution
            reviewer has to be an Avatar object.
        """
        return self._reviewerContribution.has_key(reviewer) and contribution in self._reviewerContribution[reviewer]

    def getReviewedContributions(self, reviewer):
        """ Returns the list of contributions for a given reviewer
            reviewer has to be an Avatar object.
        """
        if self._reviewerContribution.has_key(reviewer):
            return self._reviewerContribution[reviewer]
        else:
            return []

    #paper review manager methods
    def addPaperReviewManager(self, newPaperReviewManager):
        """ Adds a new paper review manager to the conference.
            newPaperReviewManager has to be an Avatar object.
            The paper review manager is sent a mail notification.
        """
        if newPaperReviewManager in self.getPaperReviewManagersList():
            raise MaKaCError("This paper review manager has already been added to this conference")
        else:
            self._paperReviewManagersList.append(newPaperReviewManager)
            newPaperReviewManager.linkTo(self._conference, "paperReviewManager")
            if not self._userCompetences.has_key(newPaperReviewManager):
                self._userCompetences[newPaperReviewManager] = []
            self.notifyModification()
        if self._enablePRMEmailNotif == True:
            notification = ConferenceReviewingNotification(newPaperReviewManager, 'Paper Review Manager', self._conference)
            GenericMailer.sendAndLog(notification, self._conference,
                                     log.ModuleNames.PAPER_REVIEWING)

    def removePaperReviewManager(self, paperReviewManager):
        """ Remove a paper review manager from the conference.
            paperReviewManager has to be an Avatar object.
            The paper review manager is sent a mail notification.
        """
        if paperReviewManager in self._paperReviewManagersList:
            if self._userCompetences.has_key(paperReviewManager):
                if not ((paperReviewManager in self._editorsList) or \
                        (paperReviewManager in self._reviewersList) or \
                        (paperReviewManager in self._refereesList)):
                    self.clearUserCompetences(paperReviewManager)
                    del(self._userCompetences[paperReviewManager])
            self._paperReviewManagersList.remove(paperReviewManager)
            paperReviewManager.unlinkTo(self._conference, "paperReviewManager")
            self.notifyModification()
            if self._enablePRMEmailNotif == True:
                notification = ConferenceReviewingRemoveNotification(paperReviewManager, 'Paper Review Manager', self._conference)
                GenericMailer.sendAndLog(notification, self._conference,
                                         log.ModuleNames.PAPER_REVIEWING)
        else:
            raise MaKaCError("Cannot remove a paper review manager who is not yet paper review manager")

    def isPaperReviewManager(self, user):
        """ Returns if a given user is paper review manager of the conference.
            user has to be an Avatar object.
        """
        return user in self._paperReviewManagersList

    def getPaperReviewManagersList(self):
        """ Returns the list of paper review managers as a list of users.
        """
        return self._paperReviewManagersList

    # templates methods
    def setTemplate(self, name, description, format, fd, id, extension = ".template"):
        """ Stores a template.
            There can be 1 template for any format.
        """

        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="MaKaC.tmp", dir = tempPath )[1]
        f = open( tempFileName, "wb" )
        f.write( fd.read() )
        f.close()

        #id = self.getNewTemplateId()

        fileName = "Contribution_template_" + id + "_c" + self._conference.id + extension

        file = conference.LocalFile()
        file.setName( fileName )
        file.setDescription( "Paper reviewing template with id " + id + "with format: " + format + " of the conference " + self._conference.id )
        file.setFileName( fileName )

        file.setFilePath( tempFileName )
        file.setOwner( self._conference )
        file.setId( fileName )
        file.archive( self._conference._getRepository() )

        self._templates[id] = Template(id, self._conference, name, description, format, file)
        self.notifyModification()

    def hasTemplates(self):
        """ Returns if the conference has any reviewing templates
        """
        return len(self._templates) > 0

    def getTemplates(self):
        """ Returns a dictionary of templates. key: id, value: Template object
        """
        return self._templates

    def getNewTemplateId(self):
        """ Returns a new an unused templateId
            Increments the templateId counter
        """
        return self._templateCounter.newCount()

    def deleteTemplate(self, id):
        """ Removes a reviewing template from the conference, given the id.
        """
        del self._templates[id]
        self.notifyModification()


    #competences methods
    def isInReviewingTeam(self, user):
        return user in self._paperReviewManagersList or \
               user in self._refereesList or \
               user in self._editorsList or \
               user in self._reviewersList or \
               user in self._reviewersList

    def setUserCompetences(self, user, competences):
        """ Sets a list of competences (a list of strings) to a given user
        """
        if self.isInReviewingTeam(user):
            self.clearUserCompetences(user)
            self.addUserCompetences(user, competences)
        else:
            raise MaKaCError("""User %s is not in the reviewing team for this conference, so you cannot set competences for him/her"""%user.getFullName())

    def clearUserCompetences(self, user):
        if self.isInReviewingTeam(user):
            for c in self.getCompetencesByUser(user):
                self._userCompetencesByTag[c].remove(user)
                if len(self._userCompetencesByTag[c]) == 0:
                        del self._userCompetencesByTag[c]
            self._userCompetences[user] = []
        else:
            raise MaKaCError("""User %s is not in the reviewing team for this conference, so you cannot clear competences for him/her"""%user.getFullName())

    def addUserCompetences(self, user, competences):
        """ Adds a list of competences (a list of strings) to a given user
        """
        if self.isInReviewingTeam(user):
            self._userCompetences[user].extend(competences)
            for c in competences:
                if self._userCompetencesByTag.has_key(c):
                    self._userCompetencesByTag[c].append(user)
                else:
                    self._userCompetencesByTag[c] = [user]
            self.notifyModification()
        else:
            raise MaKaCError("""User %s is not in the reviewing team for this conference, so you cannot add competences for him/her"""%user.getFullName())

    def removeUserCompetences(self, user, competences):
        """ Removes a list of competences (a list of strings) from a given user
        """
        if self.isInReviewingTeam(user):
            if self._userCompetences.has_key(user):
                for c in competences:
                    self._userCompetences[user].remove(c)
                    self._userCompetencesByTag[c].remove(user)
                    if len(self._userCompetencesByTag[c]) == 0:
                        del self._userCompetencesByTag[c]
                self.notifyModification()
            else:
                raise MaKaCError("""User %s does not have competences"""%(user.getFullName))
        else:
            raise MaKaCError("""User %s is not in the reviewing team for this conference, so you cannot remove competences from him/her"""%user.getFullName())

    def getAllUserCompetences(self, onlyActive = False, role = 'all'):
        """ Returns a list with the users and their competences.
            role can be 'referee', 'editor', 'reviewer' or 'all' (a different value or none specified defaults to 'all')
            The list is composed of tuples of 2 elements: (user, competenceList) where competenceList is a list of strings.
            The list is ordered by the full name of the users.
        """

        if onlyActive:
            if role == 'referee':
                users = self._refereesList
            elif role == 'editor':
                users = self._editorsList
            elif role == 'reviewer':
                users = self._reviewersList
            else:
                users = self._paperReviewManagersList + self._refereesList + self._editorsList + self._reviewersList
        else:
            if role == 'referee':
                users = [u for u in self._userCompetences.keys() if u in self._refereesList]
            elif role == 'editor':
                users = [u for u in self._userCompetences.keys() if u in self._editorsList]
            elif role == 'reviewer':
                users = [u for u in self._userCompetences.keys() if u in self._reviewersList]
            else:
                users = self._userCompetences.keys()

        users.sort(key = lambda u: u.getFullName())
        return zip(users, [self._userCompetences[user] for user in users])

    def getCompetencesByUser(self, user):
        """ Returns the list of competences (a list of strings) for a given user.
        """
        return self._userCompetences[user]

    def getUserReviewingRoles(self, user):
        """ Returns the list of roles (PRM, referee, editor, reviewer) that a given user has
            in this conference, as a list of strings.
        """
        roles=[]
        if self.isPaperReviewManager(user) and not self._choice == self.NO_REVIEWING:
            roles.append('Manager of Paper Reviewing Module')
        if self.isReferee(user) and (self._choice == self.CONTENT_REVIEWING or self._choice == self.CONTENT_AND_LAYOUT_REVIEWING):
            roles.append('Referee')
        if self.isEditor(user) and (self._choice == self.LAYOUT_REVIEWING or self._choice == self.CONTENT_AND_LAYOUT_REVIEWING):
            roles.append('Layout Reviewer')
        if self.isReviewer(user) and (self._choice == self.CONTENT_REVIEWING or self._choice == self.CONTENT_AND_LAYOUT_REVIEWING):
            roles.append('Content Reviewer')
        return roles

    def notifyModification(self):
        """ Notifies the DB that a list or dictionary attribute of this object has changed
        """
        self._p_changed = 1



class Template(Persistent):
    """ This class represents a template for contribution reviewing.
        A template is a file uploaded by a Conference Manager or a Paper Review Manager.
        Normal users can download it to have an idea of the format their contribution should have.
        A conference can have many of these templates.
    """

    formats = ["Word",
               "OpenOffice Writer",
               "PowerPoint",
               "OpenOffice Impress",
               "LaTeX"]

    def __init__(self, id, conference, name, description, format, file):
        self.__id = id
        self.__conf = conference
        self.__name = name
        self.__description = description
        self.__format = format
        self.__file = file

    def getId(self):
        return self.__id

    def getName(self):
        return self.__name

    def getDescription(self):
        return self.__description

    def getFormat(self):
        return self.__format

    def getFile(self):
        return self.__file


    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated
                in a Locator object for the category instance
        """
        loc = self.__conf.getLocator()
        loc["reviewingTemplateId"] = self.getId()
        return loc


class ConferenceReviewingNotification(GenericNotification):
    """ Template to build an email notification to a newly appointed PRM / Referee / Editor / Reviewer / Abstract Manager / Abstract Reviewer
    """

    def __init__(self, user, role, conference):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""You have been chosen as a %s for the conference "%s" """
                        % (role, conference.getTitle()))
        self.setBody("""Dear %s,

You have been chosen as a %s for the conference entitled "%s" in order to help with the paper reviewing process. Please find the Paper Reviewing utilities here:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getStraightFullName(), role, conference.getTitle(), urlHandlers.UHPaperReviewingDisplay.getURL(conference), conference.getTitle()))

class ConferenceReviewingRemoveNotification(GenericNotification):
    """ Template to build an email notification to a removed PRM / Referee / Editor / Reviewer / Abstract Manager / Abstract Reviewer
    """

    def __init__(self, user, role, conference):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""You are no longer a %s of the conference "%s" """
                        % (role, conference.getTitle()))
        self.setBody("""Dear %s,

Please, be aware that you are no longer a %s of the conference "%s":

%s

Kind regards,
Indico on behalf of "%s"
"""% ( user.getStraightFullName(),  role, conference.getTitle(), urlHandlers.UHConferenceDisplay.getURL(conference), conference.getTitle()))


class Question(Persistent, Fossilizable):

    """
    This class represents a question for the abstract/paper reviewing.
    """

    fossilizes(IReviewingQuestionFossil)

    def __init__( self, newId, text):
        """ Constructor.
            text is a string which represents the content of the question
        """
        self._id = newId
        self._text = text
        self._visible = True

    def getId(self):
        return self._id

    def getText(self):
        return self._text

    def setText(self, text):
        self._text = text


class Answer(Persistent):

    """
    This class represents an answer given of a question.
    """

    def __init__(self, newId, rbValue, numberOfAnswers, question):
        """ Constructor.
            rbValue: real value of the radio button
            scaleLower, scaleHigher and numberOfAnswers: params to calculate the value in base to the scale and
                        the number of answers
            question: Question objett associated
        """
        self._id = newId
        self._rbValue = rbValue
        self._question = question
        # is necessary to save this value (_numberOfAnswers) here because when the value is recalculated in base to a new scale
        # we need to keep the rbValue in base to the previous number of answers, otherwise if the user changes the number of radio
        # buttons as well we could have for example rbValue = 5 and numberOfAnswers = 3 (values 1, 2, 3 but never 5)
        self._numberOfAnswers = numberOfAnswers
        self._value = None # value in base to the scale limits


    def getId(self):
        return self._id

    def getValue(self):
        return self._value

    def getQuestion(self):
        return self._question

    def getRbValue(self):
        return self._rbValue

    def setRbValue(self, rbValue):
        self._rbValue = rbValue

    def calculateRatingValue(self, scaleLower, scaleHigher):
        """
        Calculate the value of the answer in base to the scale limits and the number of possible answers (radio buttons)
        """
        self._value = (((scaleHigher-scaleLower)/float(self._numberOfAnswers-1))*self._rbValue) + scaleLower



class Status(Persistent, Fossilizable):

    """
    This class represents a status for the paper reviewing.
    """

    fossilizes(IReviewingStatusFossil)

    def __init__( self, newId, name, editable):
        """ Constructor.
            name: is a string which represents the name of the status
            editable: is a boolean which represent if the status is going to be shown in the list for editing and removing options
                    (default statuses)
        """
        self._id = newId
        self._name = name
        self._editable = editable

    def getId(self):
        return self._id

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name

    def getEditable(self):
        return self._editable

    def setEditable(self, value):
        self._editable = value


