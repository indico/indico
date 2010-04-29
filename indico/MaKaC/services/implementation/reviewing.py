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
from MaKaC.reviewing import ConferenceReview
from MaKaC.services.implementation.base import ProtectedModificationService,\
    TwoListModificationBase, ParameterManager
from MaKaC.services.implementation.contribution import ContributionBase
from MaKaC.services.implementation.base import TextModificationBase
from MaKaC.services.implementation.base import HTMLModificationBase
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager,\
    RCAbstractManager, RCReferee
from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.services.implementation.base import DateTimeModificationBase
from MaKaC.webinterface.rh.contribMod import RCContributionReferee
from MaKaC.webinterface.rh.contribMod import RCContributionEditor
from MaKaC.webinterface.rh.contribMod import RCContributionReviewer
from MaKaC.webinterface.user import UserModificationBase
from MaKaC.services.implementation.base import ListModificationBase
from MaKaC import user
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.i18n import _
from MaKaC.errors import MaKaCError

import datetime


"""
Asynchronous request handlers for conference and contribution reviewing related data
"""

#####################################
###  Conference reviewing classes
#####################################

class ConferenceReviewingBase(ConferenceModifBase):
    """ This base class stores the _confReview attribute
        so that inheriting classes can use it.
    """
    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            ConferenceModifBase._checkProtection(self)
        else:
            raise ServiceError("ERR-REV1a",_("Paper Reviewing is not active for this conference"))
    
    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._confReview = self._conf.getConfReview()
            
class ConferenceReviewingPRMBase(ConferenceReviewingBase):
    """ This base class verifies that the user is a PRM
    """
    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self):
            ConferenceReviewingBase._checkProtection(self)
            
class ConferenceReviewingAMBase(ConferenceReviewingBase):
    """ This base class verifies that the user is an AM
    """
    def _checkProtection(self):
        if not RCAbstractManager.hasRights(self):
            ConferenceReviewingBase._checkProtection(self)
            
class ConferenceReviewingPRMAMBase(ConferenceReviewingBase):
    """ This base class verifies that the user is a PRM or an AM
    """
    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCAbstractManager.hasRights(self):
            ConferenceReviewingBase._checkProtection(self)
            
            
class ConferenceReviewingPRMRefereeBase(ConferenceReviewingBase):
    """ This base class verifies that the user is a PRM or a Referee of the Conference
    """
    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
            ConferenceReviewingBase._checkProtection(self)
            
            
class ConferenceReviewingAssignStaffBase(UserModificationBase, ConferenceReviewingBase):
    """ Base class for assigning referees, editors, etc. to contributions.
        It will store a list of Contribution objects in self._contributions.
        The referee, editor, etc. will be added to those contributions.
    """
    def _checkParams(self):
        UserModificationBase._checkParams(self)
        ConferenceReviewingBase._checkParams(self)
        if self._params.has_key('contributions'):
            pm = ParameterManager(self._params)
            contributionsIds = pm.extract("contributions", pType=list, allowEmpty=False)
            self._contributions = [self._conf.getContributionById(contributionId) for contributionId in contributionsIds]
        else:
            raise ServiceError("ERR-REV2",_("List of contribution ids not set"))
    
class ConferenceReviewingAssignStaffBasePRM(ConferenceReviewingAssignStaffBase):
    """ Base class that inherits from ConferenceReviewingAssignStaffBase,
        and gives modification rights only to PRMs or Managers.
    """
    
    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self):
            ProtectedModificationService._checkProtection(self)
            
class ConferenceReviewingAssignStaffBasePRMReferee(ConferenceReviewingAssignStaffBase):
    """ Base class that inherits from ConferenceReviewingAssignStaffBase,
        and gives modification rights only to PRMs or Managers or Referees (but in the last
        case, only to referees of contributions in self._contributions).
    """
    
    def _checkProtection(self):
        hasRights = False;
        if RCPaperReviewManager.hasRights(self):
            hasRights = True
        elif RCReferee.hasRights(self):
            isRefereeOfAllContributions = True
            for contribution in self._contributions:
                if not contribution.getReviewManager().isReferee(self.getAW().getUser()):
                    isRefereeOfAllContributions = False
                    break
            hasRights = isRefereeOfAllContributions
        
        if not hasRights:
            ProtectedModificationService._checkProtection(self)



class ConferenceReviewingSetupTextModificationBase(TextModificationBase, ConferenceReviewingPRMBase):
    #Note: don't change the order of the inheritance here!
    pass

class ConferenceReviewingListModificationBase (ListModificationBase, ConferenceReviewingPRMBase):
    #Note: don't change the order of the inheritance here!
    pass

class ConferenceReviewingDateTimeModificationBase (DateTimeModificationBase, ConferenceReviewingPRMBase):
    #Note: don't change the order of the inheritance here!
    pass

class ConferenceAbstractReviewingDateTimeModificationBase (DateTimeModificationBase, ConferenceReviewingAMBase):
    #Note: don't change the order of the inheritance here!
    pass
            
            
class ConferenceReviewingModeModification(ConferenceReviewingSetupTextModificationBase ):
    
    def _handleSet(self):
        self._confReview.setReviewingMode( self._value )
        
    def _handleGet(self):
        return self._confReview.getReviewingMode()
        
        
class ConferenceReviewingStatesModification(ConferenceReviewingListModificationBase):
        
    def _handleGet(self):
        return self._confReview.getStates()
    
    def _handleSet(self):
        self._confReview.setStates(self._value)
        
        
class ConferenceReviewingQuestionsModification(ConferenceReviewingListModificationBase):
        
    def _handleGet(self):
        return self._confReview.getReviewingQuestions()
    
    def _handleSet(self):
        self._confReview.setReviewingQuestions(self._value)
        
        
class ConferenceReviewingCriteriaModification(ConferenceReviewingListModificationBase):
        
    def _handleGet(self):
        return self._confReview.getLayoutCriteria()
    
    def _handleSet(self):
        self._confReview.setLayoutCriteria(self._value)
        
        
class ConferenceReviewingDefaultDueDateModification(ConferenceReviewingDateTimeModificationBase):
    
    def _checkParams(self):
        ConferenceReviewingDateTimeModificationBase._checkParams(self)
        self._dueDateToChange = self._params.get("dueDateToChange")
        
    def _setParam(self):
        if self._dueDateToChange == "Referee":
            self._conf.getConfReview().setDefaultRefereeDueDate(self._pTime)
        elif self._dueDateToChange == "Editor":
            self._conf.getConfReview().setDefaultEditorDueDate(self._pTime)
        elif self._dueDateToChange == "Reviewer":
            self._conf.getConfReview().setDefaultReviewerDueDate(self._pTime)
        else:
            raise ServiceError("ERR-REV3a",_("Kind of due date to change not set"))
        
    def _handleGet(self):
        if self._dueDateToChange == "Referee":
            date = self._conf.getConfReview().getAdjustedDefaultRefereeDueDate()
        elif self._dueDateToChange == "Editor":
            date = self._conf.getConfReview().getAdjustedDefaultEditorDueDate()
        elif self._dueDateToChange == "Reviewer":
            date = self._conf.getConfReview().getAdjustedDefaultReviewerDueDate()
        else:
            raise ServiceError("ERR-REV3b",_("Kind of due date to change not set"))
        
        if date is None:
            return 'No date set yet'
        else:
            return datetime.datetime.strftime(date,'%d/%m/%Y %H:%M')
        
        
class ConferenceAbstractReviewingDefaultDueDateModification(ConferenceAbstractReviewingDateTimeModificationBase):
    
    def _setParam(self):
        self._conf.getConfReview().setDefaultAbstractReviewerDueDate(self._pTime)
        
    def _handleGet(self):
        date = self._conf.getConfReview().getAdjustedDefaultAbstractReviewerDueDate()
        if date is None:
            return 'No date set yet'
        else:
            return datetime.datetime.strftime(date,'%d/%m/%Y %H:%M')
        
        
class ConferenceReviewingCompetenceModification(ListModificationBase, ConferenceReviewingPRMAMBase):
    #Note: don't change the order of the inheritance here!
    """ Class to change competences of users.
        Both PRMs and AMs can do this so this class inherits from ConferenceReviewingPRMAMBase.
        Note: don't change the order of the inheritance!
    """
    
    def _checkParams(self):
        ConferenceReviewingPRMAMBase._checkParams(self)
        userId = self._params.get("user", None)
        if userId:
            ph = user.PrincipalHolder()
            self._user =  ph.getById( userId )
        else:
            raise ServiceError("ERR-REV4",_("No user id specified"))
        
    def _handleGet(self):
        return self._confReview.getCompetencesByUser(self._user)
    
    def _handleSet(self):
        self._confReview.setUserCompetences(self._user, self._value)


class ConferenceReviewingReviewableMaterialsModification(TwoListModificationBase, ConferenceReviewingPRMBase):
    #Note: don't change the order of the inheritance here!
    """ Class to change which materials are to be reviewed
        Only PRMs can do this so this class inherits from ConferenceReviewingPRMBase.
        Note: don't change the order of the inheritance!
    """
        
    def _handleGet(self):
        if self._destination == "left": #left select box is the list of non-reviewable materials
            return self._confReview.getNonReviewableMaterials()
        if self._destination == "right": #right select box is the list of reviewable materials
            return self._confReview.getReviewableMaterials()
    
    def _handleSet(self):
        if self._destination == "right": #right select box is the list of reviewable materials
            self._confReview.addReviewableMaterials(self._value)
        if self._destination == "left": #left select box is the list of non-reviewable materials
            self._confReview.removeReviewableMaterials(self._value)


class ConferenceReviewingUserCompetenceList(ListModificationBase, ConferenceReviewingPRMRefereeBase):
    #Note: don't change the order of the inheritance here!
    """ Class to return all the referees / editors / reviewers of the conference,
        plus their competences.
    """
    def _checkParams(self):
        ConferenceReviewingPRMRefereeBase._checkParams(self)
        self._role = self._params.get("role", None)
        if self._role is None:
            raise ServiceError("ERR-REV5",_("No role specified"))
        
    def _handleGet(self):
        return [{"id": user.getId(), "name": user.getStraightFullName(), "competences": c}
                for user, c in self._confReview.getAllUserCompetences(True, self._role)]
        
        
        
class ConferenceReviewingAssignReferee(ConferenceReviewingAssignStaffBasePRM):
    """ Assigns a referee to a list of contributions
    """
    def _getAnswer(self):
        if not self._targetUser:
            raise ServiceError("ERR-REV6a",_("user id not set"))

        for contribution in self._contributions:
            rm = contribution.getReviewManager()
            if not rm.isReferee(self._targetUser):
                if rm.hasReferee():
                    rm.removeReferee()
                rm.setReferee(self._targetUser)
        return True
        
class ConferenceReviewingRemoveReferee(ConferenceReviewingAssignStaffBasePRM):
    """ Removes the referee from a list of contributions
    """
    def _getAnswer(self):
        for contribution in self._contributions:
            rm = contribution.getReviewManager()
            if rm.hasReferee():
                rm.removeReferee()
        return True
        
        
class ConferenceReviewingAssignEditor(ConferenceReviewingAssignStaffBasePRMReferee):
    """ Assigns an editor to a list of contributions
    """
    def _getAnswer(self):
        if not self._targetUser:
            raise ServiceError("ERR-REV6b",_("user id not set"))
        
        for contribution in self._contributions:
            rm = contribution.getReviewManager()
            if rm.hasReferee():
                if not rm.isEditor(self._targetUser):
                    if rm.hasEditor():
                        rm.removeEditor()
                    rm.setEditor(self._targetUser)
            else:
                raise ServiceError("ERR-REV9a",_("This contribution has no Referee yet"))
        return True
        
class ConferenceReviewingRemoveEditor(ConferenceReviewingAssignStaffBasePRMReferee):
    """ Removes the editor from a list of contributions
    """
    def _getAnswer(self):
        for contribution in self._contributions:
            rm = contribution.getReviewManager()
            if rm.hasEditor():
                rm.removeEditor()
        return True


class ConferenceReviewingAddReviewer(ConferenceReviewingAssignStaffBasePRMReferee):
    """ Adds a reviewer to a list of contributions
    """
    def _getAnswer(self):
        if not self._targetUser:
            raise ServiceError("ERR-REV6c",_("user id not set"))
        
        for contribution in self._contributions:
            rm = contribution.getReviewManager()
            if rm.hasReferee():
                if not rm.isReviewer(self._targetUser): 
                    rm.addReviewer(self._targetUser)
            else:
                raise ServiceError("ERR-REV9b",_("This contribution has no Referee yet"))
        return True

class ConferenceReviewingRemoveReviewer(ConferenceReviewingAssignStaffBasePRMReferee):
    """ Removes a given reviewer from a list of contributions
    """  
    def _getAnswer(self):
        if not self._targetUser:
            raise ServiceError("ERR-REV6d",_("user id not set"))
        
        for contribution in self._contributions:
            rm = contribution.getReviewManager() 
            rm.removeReviewer(self._targetUser)
        return True


class ConferenceReviewingRemoveAllReviewers(ConferenceReviewingAssignStaffBasePRMReferee):
    """ Removes all the reviewers from a list of contributions
    """  
    def _getAnswer(self):
        for contribution in self._contributions:
            contribution.getReviewManager().removeAllReviewers()
        return True



#####################################
###  Contribution reviewing classes
#####################################
class ContributionReviewingBase(ProtectedModificationService, ContributionBase):
    
    def _checkParams(self):
        ContributionBase._checkParams(self)
        self._current = self._params.get("current", None)
    
    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            hasRights = False
            if self._current == 'refereeJudgement':
                hasRights =  RCContributionReferee.hasRights(self)
            elif self._current == 'editorJudgement':
                hasRights =  RCContributionEditor.hasRights(self)
            elif self._current == 'reviewerJudgement':
                hasRights = RCContributionReviewer.hasRights(self)
            
            if not hasRights and not RCPaperReviewManager.hasRights(self):
                ProtectedModificationService._checkProtection(self)   
        else:
            raise ServiceError("ERR-REV1b",_("Paper Reviewing is not active for this conference"))
          
            
    def getJudgementObject(self):
        lastReview = self._target.getReviewManager().getLastReview() 
        if self._current == 'refereeJudgement':
            return lastReview.getRefereeJudgement()
        elif self._current == 'editorJudgement':
            return lastReview.getEditorJudgement()
        elif self._current == 'reviewerJudgement':
            return lastReview.getReviewerJudgement(self._getUser())
        else:
            raise ServiceError("ERR-REV7",_("Current kind of judgement not specified"))

class ContributionReviewingTextModificationBase (TextModificationBase, ContributionReviewingBase):
    #Note: don't change the order of the inheritance here!
    pass

class ContributionReviewingHTMLModificationBase (HTMLModificationBase, ContributionReviewingBase):
    #Note: don't change the order of the inheritance here!
    pass

class ContributionReviewingDateTimeModificationBase (DateTimeModificationBase, ContributionReviewingBase):
    #Note: don't change the order of the inheritance here!
    pass


class ContributionReviewingDueDateModification(ContributionReviewingDateTimeModificationBase):
    
    def _checkParams(self):
        ContributionReviewingDateTimeModificationBase._checkParams(self)
        self._dueDateToChange = self._params.get("dueDateToChange")
        
        
    def _setParam(self):
        lastReview = self._target.getReviewManager().getLastReview()
        if self._dueDateToChange == "Referee":
            lastReview.setRefereeDueDate(self._pTime)
        elif self._dueDateToChange == "Editor":
            lastReview.setEditorDueDate(self._pTime)
        elif self._dueDateToChange == "Reviewer":
            lastReview.setReviewerDueDate(self._pTime)
        else:
            raise ServiceError("ERR-REV3c",_("Kind of due date to change not set"))
        
    def _handleGet(self):
        lastReview = self._target.getReviewManager().getLastReview()
        if self._dueDateToChange == "Referee":
            date = lastReview.getAdjustedRefereeDueDate()
        elif self._dueDateToChange == "Editor":
            date = lastReview.getAdjustedEditorDueDate()
        elif self._dueDateToChange == "Reviewer":
            date = lastReview.getAdjustedReviewerDueDate()
        else:
            raise ServiceError("ERR-REV3d",_("Kind of due date to change not set"))
        
        return datetime.datetime.strftime(date,'%d/%m/%Y %H:%M')

class ContributionReviewingJudgementModification(ContributionReviewingTextModificationBase):
    
    def _handleSet(self):
        if self.getJudgementObject().isSubmitted():
            raise ServiceError("ERR-REV8a",_("You cannot modify a judgement marked as submitted"))
        self.getJudgementObject().setJudgement(self._value)
        
    def _handleGet(self):
        judgement = self.getJudgementObject().getJudgement()
        if judgement is None:
            return "No judgement yet"
        else:
            return judgement

class ContributionReviewingCommentsModification(ContributionReviewingHTMLModificationBase):
    
    def _handleSet(self):
        if self.getJudgementObject().isSubmitted():
            raise ServiceError("ERR-REV8b",_("You cannot modify a judgement marked as submitted"))
        self.getJudgementObject().setComments(self._value)
        
    def _handleGet(self):   
        return self.getJudgementObject().getComments()
    
class ContributionReviewingCriteriaModification(ContributionReviewingTextModificationBase):
    
    def _checkParams(self):
        ContributionReviewingTextModificationBase._checkParams(self)
        self._criterion = self._params.get("criterion")
    
    def _handleSet(self):
        if self.getJudgementObject().isSubmitted():
            raise ServiceError("ERR-REV8c",_("You cannot modify a judgement marked as submitted"))
        self.getJudgementObject().setAnswer(self._criterion, int(self._value))
        
    def _handleGet(self):
        return self.getJudgementObject().getAnswer(self._criterion)
            
    
class ContributionReviewingSetSubmitted(ContributionReviewingBase):
        
    def _getAnswer( self ):
        
        if self._params.has_key('value'):
            judgementObject = self.getJudgementObject()
            try:
                judgementObject.setSubmitted(not self.getJudgementObject().isSubmitted())
            except MaKaCError, e:
                raise ServiceError("ERR-REV9", e.getMsg())
                
            judgementObject.setAuthor(self._getUser())
            judgementObject.sendNotificationEmail(widthdrawn = not self.getJudgementObject().isSubmitted())
        return self.getJudgementObject().isSubmitted()

class ContributionReviewingCriteriaDisplay(ContributionReviewingBase):
        
    def _getAnswer( self ):
        return [str(q) + " : " + ConferenceReview.reviewingQuestionsAnswers[int(a)]
                for q,a in self.getJudgementObject().getAnswers()]
        


methodMap = {
    "conference.changeReviewingMode": ConferenceReviewingModeModification,
    "conference.changeStates": ConferenceReviewingStatesModification,
    "conference.changeQuestions": ConferenceReviewingQuestionsModification,
    "conference.changeCriteria": ConferenceReviewingCriteriaModification,
    "conference.changeCompetences": ConferenceReviewingCompetenceModification,
    "conference.changeDefaultDueDate" : ConferenceReviewingDefaultDueDateModification,
    "conference.changeAbstractReviewerDefaultDueDate" : ConferenceAbstractReviewingDefaultDueDateModification,
    "conference.changeReviewableMaterials" : ConferenceReviewingReviewableMaterialsModification,
    "conference.userCompetencesList": ConferenceReviewingUserCompetenceList,
    
    "conference.assignReferee" : ConferenceReviewingAssignReferee,
    "conference.removeReferee" : ConferenceReviewingRemoveReferee,
    "conference.assignEditor" : ConferenceReviewingAssignEditor,
    "conference.removeEditor" : ConferenceReviewingRemoveEditor,
    "conference.addReviewer" : ConferenceReviewingAddReviewer,
    "conference.removeReviewer" : ConferenceReviewingRemoveReviewer,
    "conference.removeAllReviewers" : ConferenceReviewingRemoveAllReviewers,
    
    "contribution.changeDueDate": ContributionReviewingDueDateModification,
    "contribution.changeComments": ContributionReviewingCommentsModification,
    "contribution.changeJudgement": ContributionReviewingJudgementModification,
    "contribution.changeCriteria": ContributionReviewingCriteriaModification,
    "contribution.getCriteria": ContributionReviewingCriteriaDisplay,
    "contribution.setSubmitted": ContributionReviewingSetSubmitted
    }
