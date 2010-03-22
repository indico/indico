# -*- coding: utf-8 -*-
##
## $Id: reviewing.py,v 1.15 2009/04/15 15:17:45 dmartinc Exp $
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
from datetime import datetime
from persistent import Persistent
from MaKaC.errors import MaKaCError
import tempfile
from MaKaC.common import Config
import conference
from MaKaC.common.Counter import Counter

###############################################
# Conference-wide classes
###############################################


class ConferenceReview(Persistent):
    """
    This class manages the parameters of the conference reviewing.
    """
    reviewingModes = ["", "No reviewing", "Paper reviewing", "Paper editing", "Paper editing and reviewing"]
    predefinedStates = ["Accept", "To be corrected", "Reject"]
    reviewingQuestionsAnswers = ["Strongly Disagree", "Disagree", "Weakly Disagree", "Borderline", "Weakly Agree", "Agree", "Strongly Agree"]
    reviewingQuestionsLabels = ["-3", "", "", "0", "", "", "+3"]
    initialSelectedAnswer = 3
    
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
        
        self._abstractManagerList = []
        self._abstractReviewersList = []
        
        self._refereeContribution = {} #key: user, value: list of contributions where user is referee
        self._editorContribution = {} #key: user, value: list of contributions where user is editor
        self._reviewerContribution = {} #key: user, value: list of contributions where user is reviewer
        self._reviewerAsbtract = {} #key: user, value: list of abstracts where user is abstract reviewer
        
        self.setChoice(1) #initial reviewing mode: no reviewing  
        
        #default dates
        self._startSubmissionDate = None
        self._endSubmissionDate = None
        self._defaultRefereeDueDate = None
        self._defaultEditorDueDate = None
        self._defaultReviwerDueDate = None
        self._defaultAbstractReviwerDueDate = None

        self._reviewableMaterials = ["paper"]
        from MaKaC.webinterface.materialFactories import MaterialFactoryRegistry

        self._nonReviewableMaterials = MaterialFactoryRegistry._allowedMaterials['conference'] + MaterialFactoryRegistry._allowedMaterials['category']

        self._nonReviewableMaterials.remove("paper")

        self._states = [] # list of content reviewing and final judgement non-default states
        self._reviewingQuestions = [] #list of content reviewing and final judgement questions
        self._formCriteriaList = [] #list of layout editing criteria
        self._templates = {} #dictionary with layout templates. key: id, value: Template object
        self._templateCounter = Counter(1) #counter to make new id's for the templates
        self._userCompetences = {} #dictionary with the competences of each user. key: user, value: list of competences
        self._userCompetencesByTag = {} #dictionary with the users for each competence. key: competence, value: list of users
        
        self.notifyModification()
    
    
    def getConference(self):
        """ Returns the parent conference of the ConferenceReview object
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
        
    def setDefaultAbstractReviewerDueDate(self, date):
        self._defaultAbstractReviwerDueDate = date
        
    def getDefaultAbstractReviewerDueDate(self):
        if not hasattr(self, '_defaultAbstractReviwerDueDate'):
            self._defaultAbstractReviwerDueDate = None
        return self._defaultAbstractReviwerDueDate
    
    def getAdjustedDefaultAbstractReviewerDueDate(self):
        if self.getDefaultAbstractReviewerDueDate() is None:
            return None
        else:
            return getAdjustedDate(self._defaultAbstractReviwerDueDate, self.getConference())
    
    #Reviewing mode methods
    def setChoice(self, choice):
        """ Sets the reviewing mode for the conference, as a number and as a string
            1: "No reviewing"
            2: "Paper reviewing"
            3: "Paper editing"
            4: "Paper editing and reviewing"
        """
        self._choice = choice
        self._reviewing = ConferenceReview.reviewingModes[choice]
        
    def getChoice(self):
        """ Returns the reviewing mode for the conference, as a number
            1: "No reviewing"
            2: "Paper reviewing"
            3: "Paper editing"
            4: "Paper editing and reviewing"
        """
        return self._choice
 
    def getReviewingMode(self):
        """ Returns the reviewing mode for the conference, as a string
        """
        return self._reviewing
    
    def setReviewingMode(self, mode):
        """ Sets the reviewing mode of the conference, as a string.
            The string has to be one of those in ConferenceReview.reviewingModes
        """
        if mode in ConferenceReview.reviewingModes:
            self._reviewing = mode
            self._choice = ConferenceReview.reviewingModes.index(mode)
            
    def hasReviewing(self):
        """ Convenience method that returns if the Conference has a reviewing mode active or not.
        """
        return self._choice > 1
    
    def hasPaperReviewing(self):
        """ Convenience method that returns if the Conference has a reviewing mode that allows paper reviewing.
            (modes 2 and 4)
        """
        return self._choice == 2 or self._choice == 4
    
    def hasPaperEditing(self):
        """ Convenience method that returns if the Conference has a reviewing mode that allows paper editing.
            (modes 3 and 4)
        """
        return self._choice == 3 or self._choice == 4
   
    #Choice of reviewable materials methods
    def getReviewableMaterials(self):
        """ Returns the list of reviewable materials.
            Reviewable materials are the only ones subject to versioning and they will be "blocked"
            when the author submits them, so that they cannot be changed during the reviewing process.
        """
        return self._reviewableMaterials
    
    def getNonReviewableMaterials(self):
        """ Returns the list of non-reviewable materials
        """
        return self._nonReviewableMaterials
    
    def addReviewableMaterials(self, materials):
        """ Adds a list of materials to the list of reviewable materials
        """
        self._reviewableMaterials.extend(materials)
        for m in materials:
            self._nonReviewableMaterials.remove(m)
        self.notifyModification()
            
    def removeReviewableMaterials(self, materials):
        """ Removes a list of materials from the list of reviewable materials
        """
        self._nonReviewableMaterials.extend(materials)
        for m in materials:
            self._reviewableMaterials.remove(m)
        self.notifyModification()
   
    #Content reviewing and final judgement new states methods
    def addState(self, state):
        """ Adds a state to the list of non-default states
        """
        self._states.append(state)
        self.notifyModification()

    def getStates(self):
        """ Returns list of non-default states
        """
        return self._states
    
    def setStates(self, states):
        self._states = states
    
    def getAllStates(self):
        """ Returns list of default and non-default states
        """
        return ConferenceReview.predefinedStates + self._states
    
    def removeState(self, state):
        """ Remoevs a state
        """
        if state in self._states:
            self._states.remove(state)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot remove a state which doesn't exist")
    
    
    
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
        
    # content reviewing and final judgement questions methods
    def addReviewingQuestion(self, reviewingQuestion):
        """ Adds this question at the end of the list of questions
        """
        self._reviewingQuestions.append(reviewingQuestion)
        self.notifyModification()
        
    def getReviewingQuestions(self):
        """ Returns the list of questions
        """
        return self._reviewingQuestions
    
    def setReviewingQuestions(self, questions):
        """ Set the whole list of questions
        """
        self._reviewingQuestions = questions
    
    def removeReviewingQuestion(self, reviewingQuestion):
        """ Removes a question from the list
        """
        if reviewingQuestion in self._reviewingQuestions:
            self._reviewingQuestions.remove(reviewingQuestion)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot remove a question which doesn't exist")

    # layout editing criteria methods
    def addLayoutCriteria(self, formCriteria):
        """ Add a new layout editing criterion
        """
        self._formCriteriaList.append(formCriteria)
        self.notifyModification()

    def getLayoutCriteria(self):
        """ Get the list of all the layout criteria
        """
        return self._formCriteriaList
    
    def setLayoutCriteria(self, criteria):
        """ Set the whole list of all the layout criteria
        """
        self._formCriteriaList = criteria

    def removeLayoutCriteria(self, criteria):
        """ Remove one the layout criteria
        """
        if criteria in self._formCriteriaList:
            self._formCriteriaList.remove(criteria)
            self.notifyModification()
        else:
            raise MaKaCError("Cannot remove a criteria which doesn't exist")


    #referee methods
    def addReferee(self, newReferee):
        """ Adds a new referee to the conference.
            newReferee has to be an Avatar object.
            The referee is sent a mail notification.
        """
        if newReferee in self.getRefereesList():
            raise MaKaCError("This referee has already been added to this conference")
        else:
            self._refereesList.append(newReferee)
            newReferee.linkTo(self._conference, "referee")
            if not self._userCompetences.has_key(newReferee):
                self._userCompetences[newReferee] = []
            self.notifyModification()
            notification = ConferenceReviewingNotification(newReferee, 'Referee', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", newReferee)
            

    def removeReferee(self, referee):
        """ Remove a referee from the conference.
            referee has to be an Avatar object.
            The referee is sent a mail notification.
        """
        if referee in self._refereesList:
            if self._userCompetences.has_key(referee):
                self.clearUserCompetences(referee)
                del(self._userCompetences[referee])
            self._refereesList.remove(referee)
            referee.unlinkTo(self._conference, "referee")
            self.notifyModification()
            notification = ConferenceReviewingRemoveNotification(referee, 'Referee', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", referee)
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
            The editor is sent a mail notification.
        """
        if newEditor in self.getEditorsList():
            raise MaKaCError("This editor has already been added to this conference")
        else:
            self._editorsList.append(newEditor)
            newEditor.linkTo(self._conference, "editor")
            if not self._userCompetences.has_key(newEditor):
                self._userCompetences[newEditor] = []
            self.notifyModification()
            notification = ConferenceReviewingNotification(newEditor, 'Editor', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", newEditor)

    def removeEditor(self, editor):
        """ Remove a editor from the conference.
            editor has to be an Avatar object.
            The editor is sent a mail notification.
        """
        if editor in self._editorsList:
            if self._userCompetences.has_key(editor):
                self.clearUserCompetences(editor)
                del(self._userCompetences[editor])
            self._editorsList.remove(editor)
            editor.unlinkTo(self._conference, "editor")
            self.notifyModification()
            notification = ConferenceReviewingRemoveNotification(editor, 'Editor', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", editor)
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
            The reviewer is sent a mail notification.
        """
        if newReviewer in self.getReviewersList():
            raise MaKaCError("This reviewer has already been added to this conference")
        else:
            self._reviewersList.append(newReviewer)
            newReviewer.linkTo(self._conference, "reviewer")
            if not self._userCompetences.has_key(newReviewer):
                self._userCompetences[newReviewer] = []
            self.notifyModification()
            notification = ConferenceReviewingNotification(newReviewer, 'Reviewer', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", newReviewer)
        
    def removeReviewer(self, reviewer):
        """ Remove a reviewer from the conference.
            reviewer has to be an Avatar object.
            The reviewer is sent a mail notification.
        """
        if reviewer in self._reviewersList:
            if self._userCompetences.has_key(reviewer):
                self.clearUserCompetences(reviewer)
                del(self._userCompetences[reviewer])
            self._reviewersList.remove(reviewer)
            reviewer.unlinkTo(self._conference, "reviewer")
            self.notifyModification()
            notification = ConferenceReviewingRemoveNotification(reviewer, 'Reviewer', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", reviewer)
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
            notification = ConferenceReviewingNotification(newPaperReviewManager, 'Paper Review Manager', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", newPaperReviewManager)

    def removePaperReviewManager(self, paperReviewManager):
        """ Remove a paper review manager from the conference.
            paperReviewManager has to be an Avatar object.
            The paper review manager is sent a mail notification.
        """
        if paperReviewManager in self._paperReviewManagersList:
            if self._userCompetences.has_key(paperReviewManager):
                self.clearUserCompetences(paperReviewManager)
                del(self._userCompetences[paperReviewManager])
            self._paperReviewManagersList.remove(paperReviewManager)
            paperReviewManager.unlinkTo(self._conference, "paperReviewManager")
            self.notifyModification()
            notification = ConferenceReviewingRemoveNotification(paperReviewManager, 'Paper Review Manager', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", paperReviewManager)
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
    
    #abstract manager methods
    def addAbstractManager(self, newAbstractManager):
        """ Adds a new abstract manager to the conference.
            newAbstractManager has to be an Avatar object.
            The abstract manager is sent a mail notification.
        """
        if newAbstractManager in self.getAbstractManagersList():
            raise MaKaCError("This abstract manager has already been added to this conference")
        else:
            self._abstractManagerList.append(newAbstractManager)
            newAbstractManager.linkTo(self._conference, "abstractManager")
            if not self._userCompetences.has_key(newAbstractManager):
                self._userCompetences[newAbstractManager] = []
            self.notifyModification()
            notification = ConferenceReviewingNotification(newAbstractManager, 'Abstract Manager', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", newAbstractManager)

    def removeAbstractManager(self, abstractManager):
        """ Remove a abstract manager from the conference.
            abstractManager has to be an Avatar object.
            The abstract manager is sent a mail notification.
        """
        if abstractManager in self._abstractManagerList:
            if self._userCompetences.has_key(abstractManager):
                self.clearUserCompetences(abstractManager)
                del(self._userCompetences[abstractManager])
            self._abstractManagerList.remove(abstractManager)
            abstractManager.unlinkTo(self._conference, "abstractManager")
            self.notifyModification()
            notification = ConferenceReviewingRemoveNotification(abstractManager, 'Abstract Manager', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", abstractManager)
        else:
            raise MaKaCError("Cannot remove a abstract manager who is not yet abstract manager")
        
    def isAbstractManager(self, user):
        """ Returns if a given user is abstract manager of the conference. 
            user has to be an Avatar object.
        """
        return user in self._abstractManagerList

    def getAbstractManagersList(self):
        """ Returns the list of abstract managers as a list of users.
        """
        return self._abstractManagerList
    
    #abstract reviewer methods
    def addAbstractReviewer(self, newAbstractReviewer):
        """ Adds a new abstract reviewer to the conference.
            newAbstractReviewer has to be an Avatar object.
            The abstract reviewer is sent a mail notification.
        """
        if newAbstractReviewer in self.getAbstractReviewersList():
            raise MaKaCError("This abstract reviewer has already been added to this conference")
        else:
            self._abstractReviewersList.append(newAbstractReviewer)
            newAbstractReviewer.linkTo(self._conference, "abstractReviewer")
            if not self._userCompetences.has_key(newAbstractReviewer):
                self._userCompetences[newAbstractReviewer] = []
            self.notifyModification()
            notification = ConferenceReviewingNotification(newAbstractReviewer, 'Abstract Reviewer', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", newAbstractReviewer)
        
    def removeAbstractReviewer(self, abstractReviewer):
        """ Remove a abstract reviewer from the conference.
            abstractReviwer has to be an Avatar object.
            The abstract reviewer is sent a mail notification.
        """
        if abstractReviewer in self._abstractReviewersList:
            if self._userCompetences.has_key(abstractReviewer):
                self.clearUserCompetences(abstractReviewer)
                del(self._userCompetences[abstractReviewer])
            self._abstractReviewersList.remove(abstractReviewer)
            abstractReviewer.unlinkTo(self._conference, "abstractReviewer")
            self.notifyModification()
            notification = ConferenceReviewingRemoveNotification(abstractReviewer, 'Abstract Reviewer', self._conference)
            GenericMailer.sendAndLog(notification, self._conference, "MaKaC/reviewing.py", abstractReviewer)
        else:
            raise MaKaCError("Cannot remove an abstract reviewer who is not yet abstract reviewer")
        
    def isAbstractReviewer(self, user):
        """ Returns if a given user is abstract reviewer of the conference. 
            user has to be an Avatar object.
        """
        return user in self._abstractReviewersList
    
    def getAbstractReviewersList(self):
        """ Returns the list of abstract reviewers as a list of users.
        """
        return self._abstractReviewersList
    
    def addReviewerAbstract(self, abstractReviewer, abstract):
        """ Adds the abstract to the list of abstracts for a given abstract reviewer.
            abstractReviewer has to be an Avatar object.
        """
        if self._reviewerAbstract.has_key(abstractReviewer):
            self._reviewerAbstract[abstractReviewer].append(abstract)
            self._reviewerAbstract[abstractReviewer].sort(key= lambda c: int(c.getId()))
        else:
            self._reviewerAbstract[abstractReviewer] = [abstract]
        self.notifyModification()
            
    def removeReviewerAbstract(self, abstractReviewer, abstract):
        """ Removes the contribution from the list of contributions of this reviewer
            reviewer has to be an Avatar object.
        """
        if self._reviewerAbstract.has_key(abstractReviewer):
            self._reviewerAbstract[abstractReviewer].remove(abstract)
        self.notifyModification()

    def isReviewerAbstract(self, abstractReviewer, abstract):
        """ Returns if a user is reviewer for a given contribution
            reviewer has to be an Avatar object.
        """
        return self._reviewerAbstract.has_key(abstractReviewer) and abstract in self._reviewerAbstract[abstractReviewer]
    
    def getReviewedAbstracts(self, abstractReviewer):
        """ Returns the list of abstracts for a given reviewer
            reviewer has to be an Avatar object.
        """
        if self._reviewerAbstract.has_key(abstractReviewer):
            return self._reviewerAbstract[abstractReviewer]
        else:
            return []
    
    # templates methods
    def setTemplate(self, name, description, format, fd):
        """ Stores a template.
            There can be 1 template for any format.
        """
        
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="MaKaC.tmp", dir = tempPath )[1]
        f = open( tempFileName, "wb" )
        f.write( fd.read() )
        f.close()

        if format in Template.formats:
            extension = Template.formats[format]
        else:
            extension = ".template"
        
        id = self.getNewTemplateId()
            
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
               user in self._abstractManagerList or \
               user in self._abstractReviewersList
    
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
        if self.isPaperReviewManager(user):
            roles.append('Paper Review Manager')
        if self.isReferee(user):
            roles.append('Referee')
        if self.isEditor(user):
            roles.append('Editor')
        if self.isReviewer(user):
            roles.append('Reviewer')
        if self.isAbstractManager(user):
            roles.append('Abstracts Manager')
        if self.isAbstractReviewer(user):
            roles.append('Abstract Reviewer')
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
    
    formats = {"Word":".doc",
               "OpenOffice Writer":".odt",
               "PowerPoint":".ppt",
               "OpenOffice Impress":".odp",
               "LaTeX":".tex"}
    """ This dictionary contains the different formats proposed to the uploaders.
        Also, if a template is uploaded with one of these formats, the file will have
        an appropriate extension.
    """
    
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
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""[Indico] You have been chosen as %s for the conference "%s" (id: %s)"""
                        % (role, conference.getTitle(), str(conference.getId())))
        self.setBody("""Dear Indico user,
        
        You have been chosen as %s of the conference "%s" (id: %s), in order to help with the abstract / contribution reviewing process.
        You can go to the conference main page:
        %s
        After loggin in, you will find a link under 'My Conference' where you can click to perform your new functions.
        
        Thank you for using our system.
        """ % ( role, conference.getTitle(), str(conference.getId()), urlHandlers.UHConferenceDisplay.getURL(conference)
        ))
        
class ConferenceReviewingRemoveNotification(GenericNotification):
    """ Template to build an email notification to a removed PRM / Referee / Editor / Reviewer / Abstract Manager / Abstract Reviewer
    """
    
    def __init__(self, user, role, conference):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico Mailer<%s>"%HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail())
        self.setToList([user.getEmail()])
        self.setSubject("""[Indico] You have been removed as %s of the conference "%s" (id: %s)"""
                        % (role, conference.getTitle(), str(conference.getId())))
        self.setBody("""Dear Indico user,
        
        We are sorry to inform you that you have been removed as %s of the conference "%s" (id: %s).
        
        Thank you for using our system.
        """ % ( role, conference.getTitle(), str(conference.getId())
        ))
