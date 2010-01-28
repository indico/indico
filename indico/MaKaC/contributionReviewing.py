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

from MaKaC.webinterface.mail import GenericNotification
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import urlHandlers
from MaKaC.common.mail import GenericMailer
from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc
from persistent import Persistent
from MaKaC.errors import MaKaCError
from MaKaC.reviewing import ConferenceReview
import datetime
from MaKaC.common import Config
from MaKaC.i18n import _

###############################################
# Contribution reviewing classes
###############################################

class ReviewManager(Persistent):
    """ This class is the manager for the reviewing. It keeps historical of reviews on a contribution.
        A ReviewManager object is always linked to only 1 contribution and vice-versa.
    """

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

    def getConfReview(self):
        """ Convenience method that returns the ConferenceReview object of the Conference
            to which the contribution belongs to.
        """
        return self.getConference().getConfReview()

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

    def getReviewById(self, reviewId):
        return self._versioning[int(reviewId)]
    
    
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
            self.getConfReview().addRefereeContribution(referee, self._contribution)
            self.getLastReview().setRefereeDueDate(self.getConfReview().getDefaultRefereeDueDate())
            #e-mail notification will be send when referee is assigned to contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfReview()._enableRefereeEmailNotifForContribution == True: 
                notification = ContributionReviewingNotification(referee, 'Referee', self._contribution)
                GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", referee)
    
    def removeReferee(self):
        """ Removes the referee for this contribution.
            There is no 'referee' argument because there is only 1 referee by contribution.
            The ex-referee is notified by an email.
        """

        self._referee.unlinkTo(self._contribution, "referee")
        self.getConfReview().removeRefereeContribution(self._referee, self._contribution)
        #e-mail notification will be send when referee is removed from contribution only if the manager enable the option in 'Automatic e-mails' section
        if self.getConfReview()._enableRefereeEmailNotifForContribution == True:
            notification = ContributionReviewingRemoveNotification(self._referee, 'Referee', self._contribution)
            GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", self._referee)
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
        elif self.hasReferee() or self.getConfReview().getChoice() == 3:
            self._editor = editor
            editor.linkTo(self._contribution, "editor")
            self.getConfReview().addEditorContribution(editor, self._contribution)
            self.getLastReview().setEditorDueDate(self.getConfReview().getDefaultEditorDueDate())
            #e-mail notification will be send when editor is assigned to contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfReview()._enableEditorEmailNotifForContribution == True:
                notification = ContributionReviewingNotification(editor, 'Layout Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", editor)
        else:
            raise MaKaCError("Please choose a editor before assigning an editor")

    def removeEditor(self):
        """ Removes the editor for this contribution.
            There is no 'editor' argument because there is only 1 editor by contribution.
            The ex-editor is notified by an email.
        """
        self._editor.unlinkTo(self._contribution, "editor")
        self.getConfReview().removeEditorContribution(self._editor, self._contribution)
        #e-mail notification will be send when editor is removed from contribution only if the manager enable the option in 'Automatic e-mails' section
        if self.getConfReview()._enableEditorEmailNotifForContribution == True:
            notification = ContributionReviewingRemoveNotification(self._editor, 'Layout Reviewer', self._contribution)
            GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", self._editor)
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
            self.getConfReview().addReviewerContribution(reviewer, self._contribution)
            self.getLastReview().setReviewerDueDate(self.getConfReview().getDefaultReviewerDueDate())
            if self.getLastReview().getAdviceFrom(reviewer) is None:
                self.getLastReview().addReviewerJudgement(reviewer)
                #e-mail notification will be send when reviewer is assigned to contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfReview()._enableReviewerEmailNotifForContribution == True:
                notification = ContributionReviewingNotification(reviewer, 'Content Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", reviewer)
        else:
            raise MaKaCError("Please choose a referee before assigning a reviewer")


    def removeReviewer(self, reviewer):
        """ Removes the reviewer for this contribution.
            The ex-reviewer is notified by an email.
        """
        if reviewer in self._reviewersList:
            reviewer.unlinkTo(self._contribution, "reviewer")
            self.getConfReview().removeReviewerContribution(reviewer, self._contribution)
            self._reviewersList.remove(reviewer)
            self.notifyModification()
            #e-mail notification will be send when reviewer is removed from contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfReview()._enableReviewerEmailNotifForContribution == True:
                notification = ContributionReviewingRemoveNotification(reviewer, 'Content Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", reviewer)
        
        
    def removeAllReviewers(self):
        """ Removes all the reviewers for this contribution
        """
        for reviewer in self._reviewersList:
            reviewer.unlinkTo(self._contribution, "reviewer")
            self.getConfReview().removeReviewerContribution(reviewer, self._contribution)
            self.notifyModification()
            #e-mail notification will be send when reviewers are removed from contribution only if the manager enable the option in 'Automatic e-mails' section
            if self.getConfReview()._enableReviewerEmailNotifForContribution == True:
                notification = ContributionReviewingRemoveNotification(reviewer, 'Content Reviewer', self._contribution)
                GenericMailer.sendAndLog(notification, self._contribution.getConference(), "MaKaC/reviewing.py", reviewer)
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


class Judgement(Persistent):
    """ Parent class for RefereeJudgement, EditorJudgement and ReviewerJudgement
    """        
        
    def __init__(self, review, author = None, judgement = None, comments = "", submitted = False, submissionDate = None):
        self._review = review #the parent Review object for this Judgement
        self._author = author #the user (Referee, Editor or Reviewer) author of the judgement
        self._judgement = judgement #the judgement, a string
        self._comments = comments #the comments, a string
        #a dictionary with the questions / criteria proposed and the author evaluation
        self._answers = {}
        self._submitted = submitted #boolean that indicates if the judgement has been submitted or not
        self._submissionDate = submissionDate #the date where the judgement was passed

    def getReview(self):
        return self._review

    def getReviewManager(self):
        return self._review.getReviewManager()

    def getConfReview(self):
        """ Convenience method that returns the ConferenceReview object of the Conference
            to which the judgment belongs to.
        """
        return self.getReviewManager().getConfReview()

    def getAuthor(self):
        return self._author

    def getJudgement(self):
        return self._judgement

    def getComments(self):
        return self._comments

    def getAnswers(self):
        """ To be implemented by sub-classes
            Returns a list of tuples (question, answer)
        """
        pass

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

    def setJudgement(self, judgement):
        self._judgement = judgement

    def setComments(self, comments):
        self._comments = comments

    def getAnswer(self, question):
        if not self._answers.has_key(question):
            self._answers[question] = ConferenceReview.initialSelectedAnswer
        return self._answers[question]

    def setAnswer(self, question, answer):
        self._answers[question] = answer
        self.notifyModification()

    def setSubmitted(self, submitted):
        if self._judgement is None:
            raise MaKaCError("Cannot submit an opinion without choosing the judgemenent before")
        self._submitted = submitted
        self._submissionDate = nowutc()

    def sendNotificationEmail(self, widthdrawn = False):
        """ Sends an email to the contribution's authors when the referee, editor or reviewer
            pass a judgement on the contribution and only if the manager has enabled the option in 'Automatic e-mails' section.
        """
        authorList = self.getReviewManager().getContribution().getAuthorList()
        for author in authorList:
            if widthdrawn:
                if isinstance(self, RefereeJudgement) and self.getConfReview()._enableRefereeJudgementEmailNotif == True:
                    notification = ContributionReviewingJudgementWithdrawalNotification(author, self, self.getReviewManager().getContribution())
                    GenericMailer.sendAndLog(notification, self._review.getConference(), "MaKaC/reviewing.py", author)
                if isinstance(self, EditorJudgement) and self.getConfReview()._enableEditorJudgementEmailNotif == True:
                    notification = ContributionReviewingJudgementWithdrawalNotification(author, self, self.getReviewManager().getContribution())
                    GenericMailer.sendAndLog(notification, self._review.getConference(), "MaKaC/reviewing.py", author)
                if isinstance(self, ReviewerJudgement) and self.getConfReview()._enableReviewerJudgementEmailNotif == True:
                    notification = ContributionReviewingJudgementWithdrawalNotification(author, self, self.getReviewManager().getContribution())
                    GenericMailer.sendAndLog(notification, self._review.getConference(), "MaKaC/reviewing.py", author)
            else:
                if isinstance(self, RefereeJudgement) and self.getConfReview()._enableRefereeJudgementEmailNotif == True:
                    notification = ContributionReviewingJudgementNotification(author, self, self.getReviewManager().getContribution())
                    GenericMailer.sendAndLog(notification, self._review.getConference(), "MaKaC/reviewing.py", author)
                if isinstance(self, EditorJudgement) and self.getConfReview()._enableEditorJudgementEmailNotif == True:
                    notification = ContributionReviewingJudgementNotification(author, self, self.getReviewManager().getContribution())
                    GenericMailer.sendAndLog(notification, self._review.getConference(), "MaKaC/reviewing.py", author)
                if isinstance(self, ReviewerJudgement) and self.getConfReview()._enableReviewerJudgementEmailNotif == True:
                    notification = ContributionReviewingJudgementNotification(author, self, self.getReviewManager().getContribution())
                    GenericMailer.sendAndLog(notification, self._review.getConference(), "MaKaC/reviewing.py", author)
        
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

        self.getReview().copyMaterials([m for m in self.getReviewManager().getContribution().getAllMaterialList()
                                        if m.getTitle() in self.getConfReview().getReviewableMaterials()])

        if self._judgement == "To be corrected" or self._judgement in self.getReviewManager().getConference().getConfReview().getStates():
            self.getReviewManager().newReview()

    def getAnswers(self):
        return zip(self.getConfReview().getReviewingQuestions(), (self.getAnswer(k) for k in self.getConfReview().getReviewingQuestions()))

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
        if self.getReviewManager().getConference().getConfReview().getChoice() == 3:
            Judgement.setSubmitted(self, submitted)
        
            self.getReview().copyMaterials([m for m in self.getReviewManager().getContribution().getAllMaterialList()
                                        if m.getTitle() in self.getConfReview().getReviewableMaterials()])
                                                   
            if self._judgement == "To be corrected":
                self.getReviewManager().newReview()
            
    def getAnswers(self):
        return zip(self.getConfReview().getLayoutCriteria(), (self.getAnswer(k) for k in self.getConfReview().getLayoutCriteria()))

class ReviewerJudgement(Judgement):
    def getAnswers(self):
        return zip(self.getConfReview().getReviewingQuestions(), (self.getAnswer(k) for k in self.getConfReview().getReviewingQuestions()))

class Review(Persistent):
    """This class represents the judgement of a contribution made by the referee. It contains judgement and comments
    """

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
        
    def notifyModification(self):
        """ Notifies the DB that a list or dictionary attribute of this object has changed
        """
        self._p_changed = 1

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
    
    def getConfReview(self):
        """ Convenience method that returns the ConferenceReview object of the Conference
            to which the contribution belongs to.
        """
        return self.getConference().getConfReview()
    
    def getOwner(self):
        return self.getContribution()

    def getRefereeJudgement(self):
        return self._refereeJudgement

    def getEditorJudgement(self):
        return self._editorJudgement

    def getReviewerJudgement(self, reviewer):
        return self._reviewerJudgements[reviewer]

    def getReviewingStatus(self, forAuthor = False):
        """ Returns a list of strings with a description of the current status of the review.
        """
        status = []
        if self.isAuthorSubmitted():
            if self.getConfReview().getChoice() == 3:
                if self._editorJudgement.isSubmitted():
                    status.append(_("Judged: ") + str(self._editorJudgement.getJudgement()))
                else:
                    status.append(_("Pending layout reviewer decision"))
            elif self.getConfReview().getChoice() == 4 or self.getConfReview().getChoice() == 2:
                if self._refereeJudgement.isSubmitted():
                    status.append(_("Judged: ") + str(self._refereeJudgement.getJudgement()))
                else:
                    status.append(_("Pending referee decision"))
                    if not forAuthor:
                        if self.getConfReview().getChoice() == 4:
                            if self._editorJudgement.isSubmitted():
                                status.append(_("Layout judged: ") + str(self._editorJudgement.getJudgement()))
                            else:
                                status.append(_("Pending layout reviewer decision"))
                            
                        if self.anyReviewerHasGivenAdvice():
                            for a in self.getReviewerJudgements():
                                status.append(_("Content judged: ") + str(a.getJudgement()))
                            if not self.allReviewersHaveGivenAdvice():
                                status.append(_("Some content reviewers have not decided yet"))
                        else:
                            status.append(_("No content reviewers have decided yet"))
        else:
            status.append(_("Materials not submitted yet"))
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
        
            if self._reviewManager.hasReferee() and self.getConfReview()._enableAuthorSubmittedMatRefereeEmailNotif == True:
                notification = MaterialsSubmittedNotification(self._reviewManager.getReferee(), 'Referee', self._reviewManager.getContribution())
                GenericMailer.sendAndLog(notification, self._reviewManager.getContribution().getConference(), "MaKaC/reviewing.py", self._reviewManager.getReferee())
            
            if self._reviewManager.hasEditor() and self.getConfReview()._enableAuthorSubmittedMatEditorEmailNotif == True:
                notification = MaterialsSubmittedNotification(self._reviewManager.getEditor(), 'Layout Reviewer', self._reviewManager.getContribution())
                GenericMailer.sendAndLog(notification, self._reviewManager.getContribution().getConference(), "MaKaC/reviewing.py", self._reviewManager.getEditor())

            for reviewer in self._reviewManager.getReviewersList():
                if self.getConfReview()._enableAuthorSubmittedMatReviewerEmailNotif == True:
                    notification = MaterialsSubmittedNotification(reviewer, 'Content Reviewer', self._reviewManager.getContribution())
                    GenericMailer.sendAndLog(notification, self._reviewManager.getContribution().getConference(), "MaKaC/reviewing.py", reviewer)
        
        else:
            if self._reviewManager.hasReferee() and self.getConfReview()._enableAuthorSubmittedMatRefereeEmailNotif == True:
                notification = MaterialsChangedNotification(self._reviewManager.getReferee(), self._reviewManager.getContribution())
                GenericMailer.sendAndLog(notification, self._reviewManager.getContribution().getConference(), "MaKaC/reviewing.py", self._reviewManager.getReferee())
            
            if self._reviewManager.hasEditor() and self.getConfReview()._enableAuthorSubmittedMatEditorEmailNotif == True:
                notification = MaterialsChangedNotification(self._reviewManager.getEditor(), self._reviewManager.getContribution())
                GenericMailer.sendAndLog(notification, self._reviewManager.getContribution().getConference(), "MaKaC/reviewing.py", self._reviewManager.getEditor())

            for reviewer in self._reviewManager.getReviewersList():
                if self.getConfReview()._enableAuthorSubmittedMatReviewerEmailNotif == True:
                    notification = MaterialsChangedNotification(reviewer, self._reviewManager.getContribution())
                    GenericMailer.sendAndLog(notification, self._reviewManager.getContribution().getConference(), "MaKaC/reviewing.py", reviewer)
        
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

    def copyMaterials(self, materials):
        """ Copies the materials from the contribution to this review object.
            This is done by cloning the materials, and putting the contribution as owner.
            This way, even if the author deletes materials during another review, they endure in this review.
        """
        self._materials = []
        for m in materials:
            self._materials.append(m.clone(self))

    def getMaterialById(self, materialId):
        """ Returns one of the materials of the review given its id
        """
        return self._materials[int(materialId)]

    def getLocator(self):
        """Gives back a globaly unique identification encapsulated in a Locator
           object for the Review instance
        """
        l = self.getOwner().getLocator()
        l["reviewId"] = self.getId()
        return l

    def isFullyPublic( self ):
        if hasattr(self, "_fullyPublic"):
            return self._fullyPublic
        else:
            self.setFullyPublic()
            return self._fullyPublic

    def setFullyPublic( self ):
        for mat in self.getMaterials():
            if not mat.isFullyPublic():
                self._fullyPublic = False
                return
        self._fullyPublic = True

    def updateFullyPublic( self ):
        self.setFullyPublic()
        self.getOwner().updateFullyPublic()

    def isProtected(self):
        return self.getOwner().isProtected()

    def resetAccessCache(self, UP=True, DOWN=True):
        if UP:
            self.getOwner().resetAccessCache(True, False)
        if DOWN:
            for mat in self.getMaterials():
                mat.resetAccessCache(False, True)

    def canIPAccess( self, ip ):
        return self.getOwner().canIPAccess(ip)

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
#            GenericMailer.sendAndLog(notification, self.getConference(), "MaKaC/reviewing.py", author)


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
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""[Indico] You have been chosen as %s for the contribution "%s" (id: %s)"""
                        % (role, contribution.getTitle(), str(contribution.getId())))
        self.setBody("""Dear Indico user,

        You have been chosen as %s of the contribution "%s" (id: %s) of the conference %s (id: %s).
        You can go to the contribution reviewing page:
        %s
        If you have not already, you will have to log in to see this page.

        Thank you for using our system.
        """ % ( role, contribution.getTitle(), str(contribution.getId()), conference.getTitle(),
                str(conference.getId()), urlHandlers.UHContributionModifReviewing.getURL(contribution)
        ))

class ContributionReviewingRemoveNotification(GenericNotification):
    """ Template to build an email notification to a removed PRM / Referee / Editor / Reviewer
        for a given contribution.
    """

    def __init__(self, user, role, contribution):
        conference = contribution.getConference()
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""[Indico] You have been removed as %s of the contribution "%s" (id: %s) of the conference %s (id: %s)"""
                        % (role, contribution.getTitle(), str(contribution.getId()), conference.getTitle(),str(conference.getId())))
        self.setBody("""Dear Indico user,

        We are sorry to inform you that you have been removed as %s of the contribution "%s" (id: %s).

        Thank you for using our system.
        """ % ( role, contribution.getTitle(), str(contribution.getId())
        ))

class ContributionReviewingJudgementNotification(GenericNotification):
    """ Template to build an email notification for a contribution submitter
        once the contribution has been judged
    """

    def __init__(self, user, judgement, contribution):
        
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])

        if isinstance(judgement, EditorJudgement):
            if contribution.getConference().getConfReview().getChoice() == 3:
                self.setSubject("""[Indico] Your contribution "%s" (id: %s) has been completely reviewed by the layout reviewer"""    
                            % (contribution.getTitle(), str(contribution.getId())))
                self.setBody("""Dear Indico user,
            
            Your contribution "%s" (id: %s) has been completely reviewed by the assigned layout reviewer.
            The judgement was: %s
            
            The comments of the layout reviewer were:
            "%s"
            
            Thank you for using our system.
            """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement(),
                    judgement.getComments())
            )
            else:
                self.setSubject("""[Indico] The layout of your contribution "%s" (id: %s) has been reviewed"""    
                            % (contribution.getTitle(), str(contribution.getId())))
                self.setBody("""Dear Indico user,
        
        The layout of your contribution "%s" (id: %s) has been reviewed.
        The judgement was: %s
        
        The comments of the layout reviewer were:
        "%s"

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement(),
                judgement.getComments())
        )

        elif isinstance(judgement, ReviewerJudgement):
            self.setSubject("""[Indico] The content of your contribution "%s" (id: %s) has been reviewed"""
                            % (contribution.getTitle(), str(contribution.getId())))
            self.setBody("""Dear Indico user,

        The content of your contribution "%s" (id: %s) has been reviewed.
        The judgement was: %s
        
        The comments of the content reviewer were:
        "%s"

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement(),
                judgement.getComments())
        )

        elif isinstance(judgement, RefereeJudgement):
            self.setSubject("""[Indico] Your contribution "%s" (id: %s) has been completely reviewed by the referee"""
                            % (contribution.getTitle(), str(contribution.getId())))
            self.setBody("""Dear Indico user,

        Your contribution "%s" (id: %s) has been completely reviewed by the assigned referee.
        The judgement was: %s

        The comments of the referee were:
        "%s"

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement(),
                judgement.getComments())
        )  
     
                
class ContributionReviewingJudgementWithdrawalNotification(GenericNotification):
    """ Template to build an email notification for a contribution submitter
        once the judgement of the contribution has been withdrawn.
    """

    def __init__(self, user, judgement, contribution):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])

        if isinstance(judgement, EditorJudgement):
            if contribution.getConference().getConfReview().getChoice() == 3:
                self.setSubject("""[Indico] The judgement for your contribution "%s" (id: %s) has been widthdrawn by the layout reviewer"""    
                            % (contribution.getTitle(), str(contribution.getId())))
                self.setBody("""Dear Indico user,
        
        The judgement for your contribution "%s" (id: %s) has been widthdrawn by the assigned layout reviewer.
        The judgement was: %s
        
        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement())
        )
            else:
                self.setSubject("""[Indico] The judgement for the layout of your contribution "%s" (id: %s) has been widthdrawn"""    
                            % (contribution.getTitle(), str(contribution.getId())))
                self.setBody("""Dear Indico user,
        
        The judgement for the layout of your contribution "%s" (id: %s) has been widthdrawn.
        The judgement was: %s

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement())
        )

        elif isinstance(judgement, ReviewerJudgement):
            self.setSubject("""[Indico] The judgement for the content of your contribution "%s" (id: %s) has been widthdrawn"""
                            % (contribution.getTitle(), str(contribution.getId())))
            self.setBody("""Dear Indico user,

        The judgement for the content of your contribution "%s" (id: %s) has been widthdrawn.
        The judgement was: %s

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement())
        )

        elif isinstance(judgement, RefereeJudgement):
            self.setSubject("""[Indico] The judgement for your contribution "%s" (id: %s) has been widthdrawn by the referee"""
                            % (contribution.getTitle(), str(contribution.getId())))
            self.setBody("""Dear Indico user,

        The judgement for your contribution "%s" (id: %s) has been widthdrawn by the assigned referee.
        The judgement was: %s

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), judgement.getJudgement())
        )

class MaterialsSubmittedNotification(GenericNotification):

    def __init__(self, user, role, contribution):
        conference = contribution.getConference()
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""[Indico] The author of the contribution %s (id: %s) of the conference %s has submitted his/her materials (id: %s)"""
                        % (contribution.getTitle(), str(contribution.getId()), conference.getTitle(), str(conference.getId())))
        self.setBody("""Dear Indico user,

        The author of the contribution %s (id: %s) of the conference %s (id: %s) has marked his / her materials as submitted.
        You can now start the reviewing process as a %s.


        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), conference.getTitle(), str(conference.getId()), role))

class MaterialsChangedNotification(GenericNotification):

    def __init__(self, user, contribution):
        conference = contribution.getConference()
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""[Indico] Warning: the author of the contribution %s (id: %s) of the conference %s (id: %s) has changed his/her materials """
                        % (contribution.getTitle(), str(contribution.getId()), conference.getTitle(), str(conference.getId())))
        self.setBody("""Dear Indico user,

        The author of the contribution %s (id: %s) of the conference %s (id: %s) has removed the 'submitted' mark from his / her materials.
        This means that he may have changed the content of the materials.
        Thus, you should wait until he has marked the materials again to start / continue the reviewing process.

        Thank you for using our system.
        """ % ( contribution.getTitle(), str(contribution.getId()), conference.getTitle(), str(conference.getId())))


