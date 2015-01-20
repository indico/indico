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

from collections import defaultdict
import datetime

from MaKaC.common import log
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import urlHandlers
from MaKaC.common.mail import GenericMailer
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc
from persistent import Persistent
from MaKaC.errors import MaKaCError
from MaKaC.paperReviewing import ConferencePaperReview
from indico.core.config import Config
from MaKaC.i18n import _
from MaKaC.fossils.reviewing import IReviewManagerFossil,\
    IReviewFossil, IJudgementFossil
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.paperReviewing import Answer
from MaKaC.common.Counter import Counter
from MaKaC.webinterface.urlHandlers import UHContributionDisplay, UHContributionReviewingJudgements
from indico.util.i18n import ngettext # unicode ngettext

###############################################
# Contribution reviewing classes
###############################################

class ReviewManager(Persistent, Fossilizable):
    """ This class is the manager for the reviewing. It keeps historical of reviews on a contribution.
        A ReviewManager object is always linked to only 1 contribution and vice-versa.
    """

    fossilizes(IReviewManagerFossil)

    def __init__( self, contribution ):
        """ Constructor
            contribution has to be a Contribution object (not an id)
        """
        self._contribution = contribution #the parent contribution for this ReviewManager object
        self._reviewCounter = 0 #the version number of the next new review (starts with 0)
        self._review = Review(self._reviewCounter, self) #the current review (a.k.a. last review), a Review object.
        self._versioning = [self._review] # a list of reviews, including the present one
        self._referee = None # the referee for this contribution. If None, it has not been assigned yet.
        self._editor = None # the editor for this contribution. If None, it has not been assigned yet.
        self._reviewersList = [] #the list of reviewers (there can be more than one) for this contribution.

    def getContribution(self):
        """ Returns the parent contribution for this ReviewManager object
        """
        return self._contribution

    def getConference(self):
        """ Convenience method that returns the Conference object
            to which the contribution belongs to.
        """
        return self._contribution.getConference()

    def getConfPaperReview(self):
        """ Convenience method that returns the ConferencePaperReview object of the Conference
            to which the contribution belongs to.
        """
        return self.getConference().getConfPaperReview()

    #Review methods
    def newReview(self):
        """ Creates a new Review object and saves it in the versioning list.
        """
        self._reviewCounter = self._reviewCounter + 1
        self._review = Review(self._reviewCounter, self)
        for reviewer in self._reviewersList:
            self._review.addReviewerJudgement(reviewer)
        self._versioning.append(self._review)
        self.notifyModification()

    def getLastReview(self):
        """ Returns the current review as a Review object
        """
        return self._review

    def getVersioning(self):
        """ Returns the list of reviews, current and past, as a list of Review objects.
        """
        return self._versioning

    def getVersioningLen(self):
        return len(self._versioning)

    def getReviewById(self, reviewId):
        for i in self._versioning:
            if i.getId() == int(reviewId):
                return i
        return None

    def getSortedVerioning(self):
        versioning = self._versioning
        versioning.sort(key = lambda c: c.getId(), reverse=True)
        return versioning

    def isInReviewingTeamforContribution(self, user):
        """ Returns if the user is in the reviewing team for this contribution
        """
        return self.isReferee(user) or \
               self.isEditor(user) or \
               self.isReviewer(user)


    #referee methods
    def getReferee(self):
        """ Returns the referee for this contribution
        """
        return self._referee

    def setReferee(self, referee):
        """ Sets the referee for this contribution.
            referee has to be an Avatar object.
            The referee is notified by an email.
        """
        if self.hasReferee():
            raise MaKaCError("This contribution already has a referee")
        else:
            self._referee = referee
            referee.linkTo(self._contribution, "referee")
            self.getConfPaperReview().addRefereeContribution(referee, self._contribution)
            self.getLastReview().setRefereeDueDate(self.getConfPaperReview().getDefaultRefereeDueDate())
            #e-mail notification will be send when referee is assigned to contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfPaperReview().getEnableRefereeEmailNotifForContribution():
                notification = ContributionReviewingNotification(referee, 'Referee', self._contribution)
                GenericMailer.sendAndLog(notification,
                                         self._contribution.getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)

    def removeReferee(self):
        """ Removes the referee for this contribution.
            There is no 'referee' argument because there is only 1 referee by contribution.
            The ex-referee is notified by an email.
        """

        self._referee.unlinkTo(self._contribution, "referee")
        self.getConfPaperReview().removeRefereeContribution(self._referee, self._contribution)
        if self.hasEditor():
            self.removeEditor()
        if self.hasReviewers():
            self.removeAllReviewers()
        #e-mail notification will be send when referee is removed from contribution only if the manager enable the option in 'Automatic e-mails' section
        if self.getConfPaperReview().getEnableRefereeEmailNotifForContribution():
            notification = ContributionReviewingRemoveNotification(self._referee, 'Referee', self._contribution)
            GenericMailer.sendAndLog(notification,
                                     self._contribution.getConference(),
                                     log.ModuleNames.PAPER_REVIEWING)
        self._referee = None

    def isReferee(self, user):
        """ Returns if a given user is the referee for this contribution.
            The user has to be an Avatar object.
        """
        return user is not None and user == self._referee

    def hasReferee(self):
        """ Returns if this conference has a referee already.
        """
        return self._referee is not None

    #editor methods
    def getEditor(self):
        """ Returns the editor for this contribution
        """
        return self._editor

    def setEditor(self, editor):
        """ Sets the editor for this contribution.
            editor has to be an Avatar object.
            The editor is notified by an email.
        """
        if self.hasEditor():
            raise MaKaCError("This contribution is already has an editor")
        elif self.hasReferee() or self.getConfPaperReview().getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
            self._editor = editor
            editor.linkTo(self._contribution, "editor")
            self.getConfPaperReview().addEditorContribution(editor, self._contribution)
            self.getLastReview().setEditorDueDate(self.getConfPaperReview().getDefaultEditorDueDate())
            #e-mail notification will be send when editor is assigned to contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfPaperReview().getEnableEditorEmailNotifForContribution():
                notification = ContributionReviewingNotification(editor, 'Layout Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification,
                                         self._contribution.getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)
        else:
            raise MaKaCError("Please choose a editor before assigning an editor")

    def removeEditor(self):
        """ Removes the editor for this contribution.
            There is no 'editor' argument because there is only 1 editor by contribution.
            The ex-editor is notified by an email.
        """
        self._editor.unlinkTo(self._contribution, "editor")
        self.getConfPaperReview().removeEditorContribution(self._editor, self._contribution)
        #e-mail notification will be send when editor is removed from contribution only if the manager enable the option in 'Automatic e-mails' section
        if self.getConfPaperReview().getEnableEditorEmailNotifForContribution():
            notification = ContributionReviewingRemoveNotification(self._editor, 'Layout Reviewer', self._contribution)
            GenericMailer.sendAndLog(notification,
                                    self._contribution.getConference(),
                                    log.ModuleNames.PAPER_REVIEWING)
        self._editor = None

    def isEditor(self, user):
        """ Returns if a given user is the editor for this contribution.
            The user has to be an Avatar object.
        """
        return user is not None and user == self._editor

    def hasEditor(self):
        """ Returns if this conference has a editor already.
        """
        return self._editor is not None

    #reviewer methods
    def addReviewer(self, reviewer):
        """ Adds a reviewer to this contribution.
            reviewer has to be an Avatar object.
        """
        if reviewer in self.getReviewersList():
            raise MaKaCError("This contribution is already assigned to the chosen reviewer")
        elif self.hasReferee():
            self._reviewersList.append(reviewer)
            self.notifyModification()
            reviewer.linkTo(self._contribution, "reviewer")
            self.getConfPaperReview().addReviewerContribution(reviewer, self._contribution)
            self.getLastReview().setReviewerDueDate(self.getConfPaperReview().getDefaultReviewerDueDate())
            if self.getLastReview().getAdviceFrom(reviewer) is None:
                self.getLastReview().addReviewerJudgement(reviewer)
                #e-mail notification will be send when reviewer is assigned to contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfPaperReview().getEnableReviewerEmailNotifForContribution():
                notification = ContributionReviewingNotification(reviewer, 'Content Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification,
                                         self._contribution.getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)
        else:
            raise MaKaCError("Please choose a referee before assigning a reviewer")

    def removeReviewer(self, reviewer):
        """ Removes the reviewer for this contribution.
            The ex-reviewer is notified by an email.
        """
        if reviewer in self._reviewersList:
            reviewer.unlinkTo(self._contribution, "reviewer")
            self.getConfPaperReview().removeReviewerContribution(reviewer, self._contribution)
            self._reviewersList.remove(reviewer)
            self.notifyModification()
            #e-mail notification will be send when reviewer is removed from contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfPaperReview().getEnableReviewerEmailNotifForContribution():
                notification = ContributionReviewingRemoveNotification(reviewer, 'Content Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification,
                                         self._contribution.getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)

    def removeAllReviewers(self):
        """ Removes all the reviewers for this contribution
        """
        for reviewer in self._reviewersList:
            reviewer.unlinkTo(self._contribution, "reviewer")
            self.getConfPaperReview().removeReviewerContribution(reviewer, self._contribution)
            self.notifyModification()
            #e-mail notification will be send when reviewers are removed from contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfPaperReview().getEnableReviewerEmailNotifForContribution():
                notification = ContributionReviewingRemoveNotification(reviewer, 'Content Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification,
                                         self._contribution.getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)
        del(self._reviewersList[:])

    def getReviewersList(self):
        """ Returns the list of reviewers of this contribution,
            has a list of Avatar objects.
        """
        return self._reviewersList

    def isReviewer(self, user):
        """ Returns if a given user is the reviewer for this contribution.
            The user has to be an Avatar object.
        """
        return user in self._reviewersList

    def hasReviewers(self):
        """ Returns if this conference has at least one reviewer already.
        """
        return len(self._reviewersList) > 0

    def notifyModification(self):
        """ Notifies the DB that a list or dictionary attribute of this object has changed
        """
        self._p_changed = 1


class Judgement(Persistent, Fossilizable):
    """ Parent class for RefereeJudgement, EditorJudgement and ReviewerJudgement
    """

    fossilizes(IJudgementFossil)

    def __init__(self, review, author = None, judgement = None, comments = "", submitted = False, submissionDate = None):
        self._review = review #the parent Review object for this Judgement
        self._author = author #the user (Referee, Editor or Reviewer) author of the judgement
        self._judgement = judgement #the judgement is a status object, 1:Accept, 2:To be Corrected, 3:Reject, ...others
        self._comments = comments #the comments, a string
        #a list with the Answers objects
        self._answers = []
        self._submitted = submitted #boolean that indicates if the judgement has been submitted or not
        self._submissionDate = submissionDate #the date where the judgement was passed
        self._answerCounter = Counter(1)

    def getReview(self):
        return self._review

    def getReviewManager(self):
        return self._review.getReviewManager()

    def getConfPaperReview(self):
        """ Convenience method that returns the ConferencePaperReview object of the Conference
            to which the judgment belongs to.
        """
        return self.getReviewManager().getConfPaperReview()

    def getAuthor(self):
        return self._author

    def getJudgement(self):
        if self._judgement == None:
            return None
        else:
            return self._judgement.getName()

    def getComments(self):
        return self._comments

    def getCommentsVerbose(self):
        comments = ""
        if self.getComments():
            comments="""
Please see the comments below from the reviewing team:

"%s"
"""%self.getComments()
        return comments

    def getAnswers(self):
        """ To be implemented by sub-classes
        """
        pass

    def _getAnswerCounter(self):
        try:
            if self._answerCounter:
                pass
        except AttributeError:
            self._answerCounter = Counter(1)
        return self._answerCounter


    def getNewAnswerId(self):
        """ Returns a new an unused answerId
            Increments the answerId counter
        """
        return self._getAnswerCounter().newCount()

    def getAllAnswers(self):
        return self._answers

    def isSubmitted(self):
        return self._submitted

    def getSubmissionDate(self):
        """ Returns the submission date for the review
        """
        return self._submissionDate

    def getAdjustedSubmissionDate(self):
        """ Returns a timezone-aware submission date given the conference's timezone.
        """
        return getAdjustedDate(self._submissionDate, self.getReviewManager().getConference())

    def setAuthor(self, user):
        self._author = user

    def setJudgement(self, judgementId):
        self._judgement = self.getReviewManager().getConfPaperReview().getStatusById(judgementId)

    def setComments(self, comments):
        self._comments = comments

    def getAnswer(self, questionId):
        """ Returns the Answer object if it already exists otherwise we create it
        """
        for answer in self._answers:
            if (questionId == answer.getQuestion().getId()):
                return answer
        return None

    def _getQuestionById(self, questionId):
        return self.getReviewManager().getConfPaperReview().getReviewingQuestionById(questionId)

    def createAnswer(self, questionId):
        """ Create the new object with the initial value for the rbValue
        """
        newId = self.getNewAnswerId()
        rbValue = ConferencePaperReview.initialSelectedAnswer
        numberOfAnswers = len(ConferencePaperReview.reviewingQuestionsAnswers)
        question = self._getQuestionById(questionId)
        newAnswer = Answer(newId, rbValue, numberOfAnswers, question)
        try:
            self._answers.append(newAnswer)
        except AttributeError:
            self._answers = []
            self._answers.append(newAnswer)
        self.notifyModification()
        return newAnswer

    def setAnswer(self, questionId, rbValue, numberOfAnswers):
        answer = self.getAnswer(questionId)
        if answer is None:
            answer = self.createAnswer(questionId)
        answer.setRbValue(rbValue)

    def setSubmitted(self, submitted):
        if self._judgement is None:
            raise MaKaCError("Cannot submit an opinion without choosing the judgemenent before")
        self._submitted = submitted
        self._submissionDate = nowutc()

    def purgeAnswers(self):
        """ Remove the answers of the questions that were sent but we don't need anymory because
            the questions have been removed """
        # Check if the question has been removed
        for answer in self._answers:
            if (self.getConfPaperReview().getReviewingQuestionById(answer.getQuestion().getId()) == None):
                self._answers.remove(answer)

    def sendNotificationEmail(self, withdrawn = False):
        """ Sends an email to the contribution's authors when the referee, editor or reviewer
            pass a judgement on the contribution and only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        authorList = self.getReviewManager().getContribution().getSubmitterList()
        referee = self.getReviewManager().getReferee()
        for author in authorList:
            if (isinstance(self, RefereeJudgement) and self.getConfPaperReview().getEnableRefereeJudgementEmailNotif()) \
            or (isinstance(self, EditorJudgement) and (self._review.getConference().getConfPaperReview().getChoice() == ConferencePaperReview.LAYOUT_REVIEWING or not self.getJudgement() in ["Accept", "Reject"]) and self.getConfPaperReview().getEnableEditorJudgementEmailNotif()) \
            or (isinstance(self, ReviewerJudgement) and not self.getJudgement() in ["Accept", "Reject"] and self.getConfPaperReview().getEnableReviewerJudgementEmailNotif()):
                if withdrawn:
                    notification = ContributionReviewingJudgementWithdrawalNotification(author, self, self.getReviewManager().getContribution())
                else:
                    notification = ContributionReviewingJudgementNotification(author, self, self.getReviewManager().getContribution())
                GenericMailer.sendAndLog(notification,
                                         self._review.getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)

        # We send an email to the Referee if the layout or the content reviewer has sent a judgement

        if (self.getConfPaperReview().getChoice() == 4 and isinstance(self, EditorJudgement) \
        and self.getConfPaperReview().getEnableEditorSubmittedRefereeEmailNotif()) \
        or ((self.getConfPaperReview().getChoice() == 2 or self.getConfPaperReview().getChoice() == 4) and isinstance(self, ReviewerJudgement) \
        and self.getConfPaperReview().getEnableReviewerSubmittedRefereeEmailNotif()):
            if withdrawn:
                notification = ContributionReviewingJudgementRefereeWithdrawalNotification(referee, self, self.getReviewManager().getContribution())
            else:
                notification = ContributionReviewingJudgementRefereeNotification(referee, self, self.getReviewManager().getContribution())
            GenericMailer.sendAndLog(notification,
                                     self._review.getConference(),
                                     log.ModuleNames.PAPER_REVIEWING)

    def notifyModification(self):
        """ Notifies the DB that a list or dictionary attribute of this object has changed
        """
        self._p_changed = 1


class RefereeJudgement(Judgement):

    def setSubmitted(self, submitted):
        """ Sets the final judgement for a review, since this is the Referee judgement.
            The judgement is a string among the pre-defined states (Accept, Reject, To be corrected) and
            any user-defined states.
            If it's the first time that the final judgement is set for this review, the contribution materials
            are copied into the review.
            If the judgement is 'To be corrected' or one of the user-defined states, versioning takes place.
            A new Review object is then created as 'last review'.
        """
        Judgement.setSubmitted(self, submitted)
        if (not self._submitted):
            # Check if it is necessary to purge some answers
            self.purgeAnswers()
        matReviewing = self.getReviewManager().getContribution().getReviewing()

        self.getReview().copyMaterials(matReviewing)

        # 2 --> to be corrected, > 3 has the same behaviour as 'to be corrected'
        if int(self._judgement.getId()) == 2 or int(self._judgement.getId()) > 3:
            rm = self.getReviewManager()
            rm.newReview()
            # remove reviewing materials from the contribution
            rm.getContribution().removeMaterial(matReviewing)


    def getAnswers(self):
        questionAnswerList = []
        for answer in self._answers:
            try:
                questionText = answer.getQuestion().getText()
                questionJudgement = ConferencePaperReview.reviewingQuestionsAnswers[answer.getRbValue()]
                questionAnswerList.append(questionText+": "+questionJudgement)
            except AttributeError:
                continue
        return questionAnswerList

class EditorJudgement(Judgement):

    def setSubmitted(self, submitted):
        """ Sets the final judgement for a review, if the reviewing mode is only layout reviewing
            since this is the Layout Reviewer judgement.
            The judgement is a string among the pre-defined states (Accept, Reject, To be corrected)
            If it's the first time that the final judgement is set for this review, the contribution materials
            are copied into the review.
            If the judgement is 'To be corrected', versioning takes place.
            A new Review object is then created as 'last review'.
        """
        Judgement.setSubmitted(self, submitted)
        if (not self._submitted):
            # Check if it is necessary to purge some answers
            self.purgeAnswers()
        # 1 --> Accepted, 2 --> To be corrected, 3 --> Rejected, >3 --> Custom, same behavour as To be corrected.
        if self.getReviewManager().getConference().getConfPaperReview().getChoice() == ConferencePaperReview.LAYOUT_REVIEWING and (self._judgement.getId() == "2" or int(self._judgement.getId()) > 3):
            matReviewing = self.getReviewManager().getContribution().getReviewing()
            self.getReview().copyMaterials(matReviewing)
            rm = self.getReviewManager()
            rm.newReview()
            # remove reviewing materials from the contribution
            rm.getContribution().removeMaterial(matReviewing)

    def purgeAnswers(self):
        """ Remove the answers of the questions that were sent but we don't need anymory because
            the questions have been removed """
        # Check if the question has been removed
        for answer in self._answers:
            if (self.getConfPaperReview().getLayoutQuestionById(answer.getQuestion().getId()) == None):
                self._answers.remove(answer)

    def _getQuestionById(self, questionId):
        return self.getReviewManager().getConfPaperReview().getLayoutQuestionById(questionId)

    def getAnswers(self):
        questionAnswerList = []
        for answer in self._answers:
            try:
                questionText = answer.getQuestion().getText()
                questionJudgement = ConferencePaperReview.reviewingQuestionsAnswers[answer.getRbValue()]
                questionAnswerList.append(questionText+": "+questionJudgement)
            except AttributeError:
                continue
        return questionAnswerList


class ReviewerJudgement(Judgement):

    def setSubmitted(self, submitted):
        Judgement.setSubmitted(self, submitted)
        if (not self._submitted):
            # Check if it is necessary to purge some answers
            self.purgeAnswers()

    def getAnswers(self):
        questionAnswerList = []
        for answer in self._answers:
            try:
                questionText = answer.getQuestion().getText()
                questionJudgement = ConferencePaperReview.reviewingQuestionsAnswers[answer.getRbValue()]
                questionAnswerList.append(questionText+": "+questionJudgement)
            except AttributeError:
                continue
        return questionAnswerList


class Review(Persistent, Fossilizable):
    """This class represents the judgement of a contribution made by the referee. It contains judgement and comments
    """

    fossilizes(IReviewFossil)

    def __init__( self, version, reviewManager):
        """ Constructor for the class.
            version: an integer, first version number is 0.
            reviewManager: the parent ReviewManager object
        """
        self._reviewManager = reviewManager #the parent ReviewManager object for this Review
        self._refereeJudgement = RefereeJudgement(self)
        self._editorJudgement = EditorJudgement(self)
        self._reviewerJudgements = {}

        self._isAuthorSubmitted = False #boolean that says if the author has submitted his / her materials or not
        self._version = version #the version number for this Review. Different Reviews for the same contribution have increasing version numbers.
        self._materials = [] #'snapshot' of the materials that were analyzed by the reviewing team. Copied from the Contribution materials when judgement is passed.
        self._authorComments = ""
        self._refereeDueDate = None #the Deadline where the referee has to pass his/her judgement
        self._editorDueDate = None #the Deadline where the editor has to pass his/her judgement
        self._reviewerDueDate = None #the Deadline where all the reviewers have to pass his/her judgement

    def notifyModification(self, **kwargs):
        """ Notifies the DB that a list or dictionary attribute of this object has changed
        """
        self._p_changed = 1

    def updateNonInheritingChildren(self, element, delete=False):
        pass

    def getId(self):
        """ Returns the id of this Review, which is the same as its version number
        """
        return self._version

    def getReviewManager(self):
        """ Returns the parent Review Manager object for this Review object.
        """
        return self._reviewManager

    def getContribution(self):
        """ Convenience method that returns the Contribution to which this Review belongs.
        """
        return self._reviewManager.getContribution()

    def getConference(self):
        """ Convenience method that returns the Conference to which this Review belongs.
        """
        return self._reviewManager.getContribution().getConference()

    def getConfPaperReview(self):
        """ Convenience method that returns the ConferencePaperReview object of the Conference
            to which the contribution belongs to.
        """
        return self.getConference().getConfPaperReview()

    def getOwner(self):
        return self.getContribution()

    def getRefereeJudgement(self):
        return self._refereeJudgement

    def getEditorJudgement(self):
        return self._editorJudgement

    def getReviewerJudgement(self, reviewer):
        return self._reviewerJudgements[reviewer]

    def _getReviewerStatus(self, status):
        if self.anyReviewerHasGivenAdvice():
            advices = defaultdict(int)
            for reviewer in self._reviewManager.getReviewersList():
                judgement = self._reviewManager.getLastReview().getReviewerJudgement(reviewer).getJudgement()
                if judgement != None:
                    advices[judgement] += 1
            resume = "(%s)" % ", ".join("%s %s" % (v, k.lower()) for k, v in advices.iteritems())
            status.append(_("Content assessed by %s %s %s") % (
                    sum(advices.values()), ngettext("reviewer", "reviewers", sum(advices.values())), resume))
        else:
            status.append(_("No content reviewers have decided yet"))

    def getReviewingStatus(self, forAuthor = False):
        """ Returns a list of strings with a description of the current status of the review.
        """
        status = []
        if self.isAuthorSubmitted():
            if self.getConfPaperReview().getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
                if self._editorJudgement.isSubmitted():
                    status.append(_("Assessed: ") + str(self._editorJudgement.getJudgement()))
                else:
                    status.append(_("Pending layout reviewer decision"))
            elif self.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_AND_LAYOUT_REVIEWING or self.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_REVIEWING:
                if self._refereeJudgement.isSubmitted():
                    status.append(_("Assessed: ") + str(self._refereeJudgement.getJudgement()))
                elif forAuthor:
                    status.append(_("Pending referee decision"))
                else:
                    if self.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_AND_LAYOUT_REVIEWING:
                        editor = self._reviewManager.getEditor()
                        if self._reviewManager.isEditor(editor) and self._editorJudgement.isSubmitted():
                            status.append(_("Layout assessed by ") + str(self._reviewManager.getEditor().getFullName())+ _(" as: ") + str(self._editorJudgement.getJudgement()))
                        else:
                            status.append(_("Pending layout reviewer decision"))
                        self._getReviewerStatus(status)
                    if self.getConfPaperReview().getChoice() == ConferencePaperReview.CONTENT_REVIEWING:
                        self._getReviewerStatus(status)
        else:
            status.append(_("Materials not yet submitted"))
        return status

    def isAuthorSubmitted(self):
        """ Returns if the author(s) of the contribution has marked the materials
            as submitted.
            When materials are marked as submitted, the review process can start.
        """
        return self._isAuthorSubmitted

    def setAuthorSubmitted(self, submitted):
        """ If submitted is True, it means that the author has marked the materials as submitted.
            If submitted is False, it means that the author has 'unmarked' the materials as submitted because
            he/she did some mistakes.
            In both cases, all the already chosen reviewing staff are notified with an email
            only if the manager has enabled the option in 'Automatic e-mails' section.
        """

        self._isAuthorSubmitted = submitted

        if submitted:

            if self._reviewManager.hasReferee() and self.getConfPaperReview().getEnableAuthorSubmittedMatRefereeEmailNotif():
                notification = MaterialsSubmittedNotification(self._reviewManager.getReferee(), 'Referee', self._reviewManager.getContribution())
                GenericMailer.sendAndLog(notification,
                                         self._reviewManager.getContribution().getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)

            if self._reviewManager.hasEditor() and self.getConfPaperReview().getEnableAuthorSubmittedMatEditorEmailNotif():
                notification = MaterialsSubmittedNotification(self._reviewManager.getEditor(), 'Layout Reviewer', self._reviewManager.getContribution())
                GenericMailer.sendAndLog(notification,
                                         self._reviewManager.getContribution().getConference(),
                                         log.ModuleNames.PAPER_REVIEWING)

            for reviewer in self._reviewManager.getReviewersList():
                if self.getConfPaperReview().getEnableAuthorSubmittedMatReviewerEmailNotif():
                    notification = MaterialsSubmittedNotification(reviewer, 'Content Reviewer', self._reviewManager.getContribution())
                    GenericMailer.sendAndLog(notification,
                                             self._reviewManager.getContribution().getConference(),
                                             log.ModuleNames.PAPER_REVIEWING)

    def getVersion(self):
        """ Returns the version number for this review. The version number is an integer, starting by 0.
        """
        return self._version

    def setAuthorComments(self, authorComments):
        self._authorComments = authorComments

    def getAuthorComments(self):
        return self._authorComments


    #review materials methods, and methods necessary for material retrieval to work
    def getMaterials(self):
        """ Returns the materials stored in this Review.
        """
        return self._materials

    def copyMaterials(self, material):
        """ Copies the materials from the contribution to this review object.
            This is done by cloning the materials, and putting the contribution as owner.
            This way, even if the author deletes materials during another review, they endure in this review.
        """
        self._materials = [material.clone(self)]

    def getMaterialById(self, materialId=0):
        """ Returns one of the materials of the review given its id

            So far there is just one material (reviewing) with many resources. So, by default we
            get the first element of the list of materials.
        """
        return self._materials[int(materialId)]

    def getLocator(self):
        """Gives back a globaly unique identification encapsulated in a Locator
           object for the Review instance
        """
        l = self.getOwner().getLocator()
        l["reviewId"] = self.getId()
        return l

    def isProtected(self):
        return self.getOwner().isProtected()

    def canIPAccess( self, ip ):
        return self.getOwner().canIPAccess(ip)

    def canUserModify( self, aw ):
        return self.getOwner().canUserModify(aw)

    #Advices methods
    def addReviewerJudgement(self, reviewer):#, questions, adviceJudgement, comments):
        """ Adds an ReviewerJudgement object to the list of ReviewerJudgements objects of the review.
            Each ReviewerJudgement object represents the opinion of a content reviewer.
        """
        self._reviewerJudgements[reviewer] = ReviewerJudgement(self, author = reviewer)
        self.notifyModification()

    def hasGivenAdvice(self, reviewer):
        """ Returns if a given user has given advice on the content of the contribution.
        """
        answer = (reviewer in self._reviewerJudgements) and (self._reviewerJudgements[reviewer].isSubmitted())
        return answer

    def getAdviceFrom(self, reviewer):
        """ Returns an the advice information from a given reviewer,
            as an Advice object.
            If the given reviewer doesn't have an Advice object yet, None is returned.
        """
        return self._reviewerJudgements.get(reviewer, None)

    def anyReviewerHasGivenAdvice(self):
        """ Returns if at least 1 reviewer has already given advice on the content of the contribution.
        """
        for reviewer in self._reviewManager.getReviewersList():
            if self.hasGivenAdvice(reviewer):
                return True

        return False

    def allReviewersHaveGivenAdvice(self):
        """ Returns if all reviewers have already given advice on the content of the contribution.
        """
        for reviewer in self._reviewManager.getReviewersList():
            if not self.hasGivenAdvice(reviewer):
                return False

        return len(self._reviewManager.getReviewersList()) > 0

    def getReviewerJudgements(self):
        """ Returns the advices from the reviewers.
        """
        return self._reviewerJudgements.values()

    def getSubmittedReviewerJudgement(self):
        """ Returns the advices from the reviewers, but only those that have been marked as submitted
        """
        return filter(lambda advice:advice.isSubmitted(), self.getReviewerJudgements())

#    #notification email methods
#    def sendNotificationEmail(self, judgement):
#        """ Sends an email to the contribution's authors when the referee, editor or reviewer
#            pass a judgement on the contribution.
#        """
#        authorList = self._reviewManager.getContribution().getAuthorList()
#        for author in authorList:
#            notification = ContributionReviewingJudgementNotification(author, judgement, self._reviewManager.getContribution())
#            GenericMailer.sendAndLog(notification, self.getConference(), "Reviewing", author)


    #dates methods
    def setRefereeDueDate(self, date):
        """ Sets the Deadline for the referee.
        """
        self._refereeDueDate = date #datetime(year, month, day, 0, 0, 0, tzinfo=timezone(self.getConference().getTimezone()))

    def getRefereeDueDate(self):
        """ Returns the Deadline for the referee
        """
        return self._refereeDueDate

    def getAdjustedRefereeDueDate(self):
        """ Returns a timezeone-aware Deadline for the referee given the conference's timezone.
        """
        if self.getRefereeDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._refereeDueDate, self.getConference())

    def getAdjustedRefereeDueDateFormatted(self):
        """ Returns a timezeone-aware Deadline for the referee given the conference's timezone,
            formatted to a string (this method is necessary due to syntax limitations of @Retrieve )
        """
        date = self.getAdjustedRefereeDueDate()
        if date:
            return datetime.datetime.strftime(date,'%d/%m/%Y %H:%M')
        else:
            return None

    def setEditorDueDate(self, date):
        """ Sets the Deadline for the editor.
        """
        self._editorDueDate = date #datetime(year, month, day, 0, 0, 0, tzinfo=timezone(self.getConference().getTimezone()))

    def getEditorDueDate(self):
        """ Returns the Deadline for the editor
        """
        return self._editorDueDate

    def getAdjustedEditorDueDate(self):
        """ Returns a timezeone-aware Deadline for the editor given the conference's timezone.
        """
        if self.getEditorDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._editorDueDate, self.getConference())

    def setReviewerDueDate(self, date):
        """ Sets the Deadline for all the reviewers.
        """
        self._reviewerDueDate = date #datetime(year, month, day, 0, 0, 0, tzinfo=timezone(self.getConference().getTimezone()))

    def getReviewerDueDate(self):
        """ Returns the Deadline for all the reviewers.
        """
        return self._reviewerDueDate

    def getAdjustedReviewerDueDate(self):
        """ Returns a timezeone-aware Deadline for all the reviewers given the conference's timezone.
        """
        if self.getReviewerDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._reviewerDueDate, self.getConference())

    def setModificationDate(self):
        """Update the modification date (of type 'datetime') to now."""
        self.modificationDate = nowutc()

######################################
# Email notification classes
######################################
class ContributionReviewingNotification(GenericNotification):
    """ Template to build an email notification to a newly appointed PRM / Referee / Editor / Reviewer
        for a given contribution.
    """

    def __init__(self, user, role, contribution):
        GenericNotification.__init__(self)
        conference = contribution.getConference()
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""You have been chosen as a %s for "%s" """% (role, conference.getTitle()))

        if role == 'Referee':
            urlh = urlHandlers.UHConfModifListContribToJudge
        elif role == 'Layout Reviewer':
            urlh = urlHandlers.UHConfModifListContribToJudgeAsEditor
        elif role == 'Content Reviewer':
            urlh = urlHandlers.UHConfModifListContribToJudgeAsReviewer

        self.setBody("""Dear %s,

You have been chosen as a %s for the paper entitled "%s" (id: %s) for the conference "%s". Please find the %s utilities here:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getStraightFullName(), role, contribution.getTitle(), str(contribution.getId()),
        conference.getTitle(), role, urlh.getURL(contribution), conference.getTitle()))

class ContributionReviewingRemoveNotification(GenericNotification):
    """ Template to build an email notification to a removed PRM / Referee / Editor / Reviewer
        for a given contribution.
    """

    def __init__(self, user, role, contribution):
        GenericNotification.__init__(self)
        conference = contribution.getConference()
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""You are no longer a %s of a paper for "%s" """ % (role, conference.getTitle()))
        self.setBody("""Dear %s,

Please, be aware that you are no longer a %s of the paper entitled "%s" (id: %s) for the conference "%s":

%s

Kind regards,
Indico on behalf of "%s"
""" % (  user.getStraightFullName(), role, contribution.getTitle(), str(contribution.getId()), conference.getTitle(), str(urlHandlers.UHConferenceDisplay.getURL(conference)), conference.getTitle()))

class ContributionReviewingJudgementNotification(GenericNotification):
    """ Template to build an email notification for a contribution submitter
        once the contribution has been judged
    """

    def __init__(self, user, judgement, contribution):
        GenericNotification.__init__(self)
        conference = contribution.getConference()
        self.setFromAddr("Indico <%s>"%Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setBCCList([judgement.getAuthor().getEmail()])

        if isinstance(judgement, EditorJudgement):
            if conference.getConfPaperReview().getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
                if judgement.getJudgement() in ["Accept", "Reject"]:
                    self.setAcceptedRejected(user, judgement, contribution, conference, "Layout Reviewer")
                else:
                    self.setFullyReviewed(user, judgement, contribution, conference, "Layout Reviewer")
            elif not judgement.getJudgement() in ["Accept", "Reject"]:
                self.setPartiallyReviewed(user, judgement, contribution, conference, "Layout")
        elif isinstance(judgement, ReviewerJudgement) and not judgement.getJudgement() in ["Accept", "Reject"]:
                self.setPartiallyReviewed(user, judgement, contribution, conference, "Content")
        elif isinstance(judgement, RefereeJudgement):
            if judgement.getJudgement() in ["Accept", "Reject"]:
                self.setAcceptedRejected(user, judgement, contribution, conference, "Referee")
            else:
                self.setFullyReviewed(user, judgement, contribution, conference, "Referee")

    def setFullyReviewed(self, user, judgement, contribution, conference, role):
        self.setSubject("""Your paper "%s" for "%s" has been completely reviewed """
                    % (contribution.getTitle(), conference.getTitle()))
        self.setBody("""Dear %s,

The %s has reviewed your paper entitled "%s" (id: %s), submitted for "%s".
The assessment is as follows: %s.
%s
You may then apply the requested modifications to your paper and submit the modified version for review. In order to do so, please proceed to your paper page:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getDirectFullNameNoTitle(upper=False), role, contribution.getTitle(), str(contribution.getId()),
         conference.getTitle(), judgement.getJudgement(), judgement.getCommentsVerbose(), UHContributionDisplay.getURL(contribution), conference.getTitle()))


    def setPartiallyReviewed(self, user, judgement, contribution, conference, typeR):
                self.setSubject("""%s Assessment of your paper "%s" for "%s" """
                            % (typeR, contribution.getTitle(), conference.getTitle()))
                self.setBody("""Dear %s,

The assigned %s Reviewer has partially reviewed your paper entitled "%s" (id: %s) submitted for "%s".
The assessment is as follows: %s.
%s

Note that this is a partial review, a final assessment will be done by the referee. In the meanwhile, you may access all the information about your paper from the following page:

%s

Kind regards,
Indico on behalf of "%s"
"""  % ( user.getDirectFullNameNoTitle(upper=False),typeR, contribution.getTitle(), str(contribution.getId()),
         conference.getTitle(), judgement.getJudgement(), judgement.getCommentsVerbose(), UHContributionDisplay.getURL(contribution), conference.getTitle()))

    def setAcceptedRejected(self, user, judgement, contribution, conference, role):
        if judgement.getJudgement() == "Accept":
            judgementText = "ACCEPTED"
        elif judgement.getJudgement() == "Reject":
            judgementText = "REJECTED"
        self.setSubject("""Your paper "%s" for "%s" has been completely reviewed"""
                            % (contribution.getTitle(), conference.getTitle()))
        self.setBody("""Dear %s,

The %s has %s your paper entitled "%s" (id: %s), submitted for "%s".
%s
You may proceed to your paper page:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getDirectFullNameNoTitle(upper=False), role, judgementText, contribution.getTitle(), str(contribution.getId()),
         conference.getTitle(), judgement.getCommentsVerbose(), UHContributionDisplay.getURL(contribution), conference.getTitle()))

class ContributionReviewingJudgementWithdrawalNotification(GenericNotification):
    """ Template to build an email notification for a contribution submitter
        once the judgement of the contribution has been withdrawn.
    """

    def __init__(self, user, judgement, contribution):
        GenericNotification.__init__(self)
        conference = contribution.getConference()
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setBCCList([judgement.getAuthor().getEmail()])
        if isinstance(judgement, RefereeJudgement):
            typeR = "Referee"
        elif isinstance(judgement, EditorJudgement):
            typeR = "Layout Reviewer"
        elif isinstance(judgement, ReviewerJudgement):
            typeR = "Content Reviewer"
        self.setSubject(""""%s" has been put back into reviewing by the %s """ % (contribution.getTitle(), typeR))
        self.setBody("""Dear %s,

Your paper entitled  "%s" (id: %s) submitted for "%s" has been put back into reviewing by the assigned %s:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getDirectFullNameNoTitle(upper=False), contribution.getTitle(), str(contribution.getId()),
        conference.getTitle(), typeR, urlHandlers.UHContributionDisplay.getURL(contribution), conference.getTitle())
        )

class ContributionReviewingJudgementRefereeNotification(GenericNotification):
    """ Template to build an email notification for a referee
        once the contribution has been judged
    """

    def __init__(self, user, judgement, contribution):
        GenericNotification.__init__(self)
        conference = contribution.getConference()
        self.setFromAddr("Indico <%s>"%Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        if isinstance(judgement, EditorJudgement):
            typeR = "Layout"
        elif isinstance(judgement, ReviewerJudgement):
            typeR = "Content"

        self.setSubject("""%s Assessment of the paper "%s" for "%s" """% (typeR, contribution.getTitle(), conference.getTitle()))
        self.setBody("""Dear %s,

The assigned %s Reviewer, %s, has partially reviewed the paper entitled "%s" (id: %s) submitted for "%s".
The assessment is as follows: %s.
%s
You may proceed to the Referee Area for this paper:

%s

Kind regards,
Indico on behalf of "%s"
"""  % ( user.getStraightFullName(), typeR, judgement.getAuthor().getStraightFullName(), contribution.getTitle(),
         str(contribution.getId()),conference.getTitle(), judgement.getJudgement(), judgement.getCommentsVerbose(),
         UHContributionReviewingJudgements.getURL(contribution), conference.getTitle()))

class ContributionReviewingJudgementRefereeWithdrawalNotification(GenericNotification):
    """ Template to build an email notification for a contribution submitter
        once the judgement of the contribution has been withdrawn.
    """

    def __init__(self, user, judgement, contribution):
        GenericNotification.__init__(self)
        conference = contribution.getConference()
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])

        if isinstance(judgement, EditorJudgement):
            typeR = "Layout"
        elif isinstance(judgement, ReviewerJudgement):
            typeR = "Content"
        self.setSubject(""""%s" has been put back into reviewing by the %s Reviewer"""% (contribution.getTitle(), typeR))
        self.setBody("""Dear %s,

The paper entitled "%s" (id: %s) submitted for "%s" has been put back into reviewing by the assigned %s Reviewer:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getStraightFullName(), contribution.getTitle(), str(contribution.getId()),conference.getTitle(),
        typeR, urlHandlers.UHConfModifListContribToJudge.getURL(contribution), conference.getTitle()))

class MaterialsSubmittedNotification(GenericNotification):

    def __init__(self, user, role, contribution):
        conference = contribution.getConference()
        GenericNotification.__init__(self)
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""An author has submitted a paper for "%s" """%  conference.getTitle())

        if role == 'Referee':
            urlh = urlHandlers.UHConfModifListContribToJudge
        elif role == 'Layout Reviewer':
            urlh = urlHandlers.UHConfModifListContribToJudgeAsEditor
        elif role == 'Content Reviewer':
            urlh = urlHandlers.UHConfModifListContribToJudgeAsReviewer

        self.setBody("""Dear %s,

An author has submitted a paper entitled "%s" (id: %s) for the conference "%s". You can now start the reviewing process as a %s:

%s

Kind regards,
Indico on behalf of "%s"
""" % ( user.getStraightFullName(), contribution.getTitle(), str(contribution.getId()), conference.getTitle(), role, urlh.getURL(contribution), conference.getTitle()))
