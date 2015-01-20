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
from MaKaC.paperReviewing import ConferencePaperReview
from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.services.implementation.contribution import ContributionBase
from MaKaC.services.implementation.base import TextModificationBase
from MaKaC.services.implementation.base import HTMLModificationBase
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager,\
    RCReferee
from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.services.implementation.base import DateTimeModificationBase
from MaKaC.webinterface.rh.contribMod import RCContributionReferee
from MaKaC.webinterface.rh.contribMod import RCContributionEditor
from MaKaC.webinterface.rh.contribMod import RCContributionReviewer
from MaKaC.webinterface.user import UserModificationBase, UserListModificationBase
from MaKaC.services.implementation.base import ListModificationBase
from MaKaC import user
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError
from MaKaC.i18n import _
from MaKaC.errors import MaKaCError
import datetime
from MaKaC.common.mail import GenericMailer
from MaKaC.contributionReviewing import ReviewManager
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.reviewing import IReviewingQuestionFossil

"""
Asynchronous request handlers for conference and contribution reviewing related data
"""

#####################################
###  Conference reviewing classes
#####################################

class ConferenceReviewingBase(ConferenceModifBase):
    """ This base class stores the _confPaperReview attribute
        so that inheriting classes can use it.
    """
    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            ConferenceModifBase._checkProtection(self)
        else:
            raise ServiceError("ERR-REV1a",_("Paper Reviewing is not active for this conference"))

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self._confPaperReview = self._conf.getConfPaperReview()
        self._confAbstractReview = self._conf.getConfAbstractReview()

class ConferenceReviewingPRMBase(ConferenceReviewingBase):
    """ This base class verifies that the user is a PRM
    """
    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self):
            ConferenceReviewingBase._checkProtection(self)


class ConferenceReviewingPRMRefereeBase(ConferenceReviewingBase):
    """ This base class verifies that the user is a PRM or a Referee of the Conference
    """
    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
            ConferenceReviewingBase._checkProtection(self)


class ConferenceReviewingAssignStaffBase(ConferenceReviewingBase, UserModificationBase):
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


class ConferenceReviewingDateTimeModificationBase (DateTimeModificationBase, ConferenceReviewingPRMBase):
    #Note: don't change the order of the inheritance here!
    pass


class ConferenceReviewingModeModification(ConferenceReviewingSetupTextModificationBase ):

    def _handleSet(self):
        self._confPaperReview.setReviewingMode( self._value )

    def _handleGet(self):
        return self._confPaperReview.getReviewingMode()


class ConferenceReviewingDeleteTemplate(ConferenceReviewingBase):

    def _getAnswer(self):
            templateId = self._params.get("templateId")
            self._confPaperReview.deleteTemplate(templateId)
            return True

class ConferenceReviewingDefaultDueDateModification(ConferenceReviewingPRMBase):

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._dueDateToChange = self._params.get("dueDateToChange")
        pm = ParameterManager(self._params.get('value'), timezone=self._conf.getTimezone())
        self._date = pm.extract('date', pType=datetime.datetime)
        self._apply = pm.extract('applyToContributions', pType=bool)

    def _setParam(self):
        if self._dueDateToChange == "Referee":
            self._conf.getConfPaperReview().setDefaultRefereeDueDate(self._date)
            return self._conf.getConfPaperReview().getAdjustedDefaultRefereeDueDate()
        elif self._dueDateToChange == "Editor":
            self._conf.getConfPaperReview().setDefaultEditorDueDate(self._date)
            return self._conf.getConfPaperReview().getAdjustedDefaultEditorDueDate()
        elif self._dueDateToChange == "Reviewer":
            self._conf.getConfPaperReview().setDefaultReviewerDueDate(self._date)
            return self._conf.getConfPaperReview().getAdjustedDefaultReviewerDueDate()
        else:
            raise ServiceError("ERR-REV3a",_("Kind of deadline to change not set"))

    def _getAnswer(self):
        date = self._setParam()
        if self._apply:
            for contrib in self._conf.getContributionList():
                lastReview = contrib.getReviewManager().getLastReview()
                if self._dueDateToChange == "Referee":
                    lastReview.setRefereeDueDate(date)
                elif self._dueDateToChange == "Editor":
                    lastReview.setEditorDueDate(date)
                elif self._dueDateToChange == "Reviewer":
                    lastReview.setReviewerDueDate(date)
                else:
                    raise ServiceError("ERR-REV3c",_("Kind of deadline to change not set"))
        if date:
            return datetime.datetime.strftime(date,'%d/%m/%Y %H:%M')
        else:
            return _("Date has not been set yet.")


class ConferenceReviewingAutoEmailsModificationPRM(ConferenceReviewingSetupTextModificationBase ):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enablePRMEmailNotif()
        else:
            self._confPaperReview.disablePRMEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnablePRMEmailNotif()

class ConferenceReviewingAutoEmailsModificationReferee(ConferenceReviewingSetupTextModificationBase ):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableRefereeEmailNotif()
        else:
            self._confPaperReview.disableRefereeEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableRefereeEmailNotif()

class ConferenceReviewingAutoEmailsModificationEditor(ConferenceReviewingSetupTextModificationBase ):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableEditorEmailNotif()
        else:
            self._confPaperReview.disableEditorEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableEditorEmailNotif()

class ConferenceReviewingAutoEmailsModificationReviewer(ConferenceReviewingSetupTextModificationBase ):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableReviewerEmailNotif()
        else:
            self._confPaperReview.disableReviewerEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableReviewerEmailNotif()

class ConferenceReviewingAutoEmailsModificationRefereeForContribution(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableRefereeEmailNotifForContribution()
        else:
            self._confPaperReview.disableRefereeEmailNotifForContribution()

    def _handleGet(self):
        return self._confPaperReview.getEnableRefereeEmailNotifForContribution()

class ConferenceReviewingAutoEmailsModificationEditorForContribution(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableEditorEmailNotifForContribution()
        else:
            self._confPaperReview.disableEditorEmailNotifForContribution()

    def _handleGet(self):
        return self._confPaperReview.getEnableEditorEmailNotifForContribution()

class ConferenceReviewingAutoEmailsModificationReviewerForContribution(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableReviewerEmailNotifForContribution()
        else:
            self._confPaperReview.disableReviewerEmailNotifForContribution()

    def _handleGet(self):
        return self._confPaperReview.getEnableReviewerEmailNotifForContribution()

class ConferenceReviewingAutoEmailsModificationRefereeJudgement(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableRefereeJudgementEmailNotif()
        else:
            self._confPaperReview.disableRefereeJudgementEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableRefereeJudgementEmailNotif()

class ConferenceReviewingAutoEmailsModificationEditorJudgement(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableEditorJudgementEmailNotif()
        else:
            self._confPaperReview.disableEditorJudgementEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableEditorJudgementEmailNotif()

class ConferenceReviewingAutoEmailsModificationReviewerJudgement(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableReviewerJudgementEmailNotif()
        else:
            self._confPaperReview.disableReviewerJudgementEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableReviewerJudgementEmailNotif()

class ConferenceReviewingAutoEmailsModificationAuthorSubmittedMatReferee(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableAuthorSubmittedMatRefereeEmailNotif()
        else:
            self._confPaperReview.disableAuthorSubmittedMatRefereeEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableAuthorSubmittedMatRefereeEmailNotif()

class ConferenceReviewingAutoEmailsModificationAuthorSubmittedMatEditor(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableAuthorSubmittedMatEditorEmailNotif()
        else:
            self._confPaperReview.disableAuthorSubmittedMatEditorEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableAuthorSubmittedMatEditorEmailNotif()

class ConferenceReviewingAutoEmailsModificationAuthorSubmittedMatReviewer(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableAuthorSubmittedMatReviewerEmailNotif()
        else:
            self._confPaperReview.disableAuthorSubmittedMatReviewerEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableAuthorSubmittedMatReviewerEmailNotif()


class ConferenceReviewingAutoEmailsModificationEditorSubmittedReferee(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableEditorSubmittedRefereeEmailNotif()
        else:
            self._confPaperReview.disableEditorSubmittedRefereeEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableEditorSubmittedRefereeEmailNotif()


class ConferenceReviewingAutoEmailsModificationReviewerSubmittedReferee(ConferenceReviewingSetupTextModificationBase):

    def _handleSet(self):
        if self._value:
            self._confPaperReview.enableReviewerSubmittedRefereeEmailNotif()
        else:
            self._confPaperReview.disableReviewerSubmittedRefereeEmailNotif()

    def _handleGet(self):
        return self._confPaperReview.getEnableReviewerSubmittedRefereeEmailNotif()


class ConferenceReviewingCompetenceModification(ListModificationBase, ConferenceReviewingPRMBase):
    #Note: don't change the order of the inheritance here!
    """ Class to change competences of users.
        Both PRMs and AMs can do this so this class inherits from ConferenceReviewingPRMBase.
        Note: don't change the order of the inheritance!
    """

    def __init__(self, *params):
        ConferenceReviewingPRMBase.__init__(self, *params)

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        userId = self._params.get("user", None)
        if userId:
            ph = user.PrincipalHolder()
            self._user =  ph.getById( userId )
        else:
            raise ServiceError("ERR-REV4",_("No user id specified"))

    def _handleGet(self):
        return self._confPaperReview.getCompetencesByUser(self._user)

    def _handleSet(self):
        self._confPaperReview.setUserCompetences(self._user, self._value)

class ConferenceReviewingContributionsAttributeList(ListModificationBase, ConferenceReviewingPRMRefereeBase):
    #Note: don't change the order of the inheritance here!
    """ Class to return all the tracks or sessions or types of the conference
    """

    def __init__(self, *params):
        ConferenceReviewingPRMRefereeBase.__init__(self, *params)

    def _checkParams(self):
        ConferenceReviewingPRMRefereeBase._checkParams(self)
        self._attribute = self._params.get("attribute", None)
        if self._attribute is None:
            raise ServiceError("ERR-REV5",_("No type/session/track specified"))

    def _handleGet(self):
        attributes = []
        for c in self._conf.getContributionList():
            if self._attribute == 'type':
                if c.getType() is not None and c.getType() not in attributes:
                    attributes.append(c.getType())
            elif self._attribute == 'track':
                if c.getTrack() is not None and c.getTrack() not in attributes:
                    attributes.append(c.getTrack())
            elif self._attribute == 'session':
                if c.getSession() is not None and c.getSession() not in attributes:
                    attributes.append(c.getSession())
            else:
                raise ServiceError("ERR-REV5",_("No attribute specified"))

        if self._attribute == 'type':
            return [{"id": attribute.getId(), "title": attribute.getName()}
                for attribute in attributes]
        else:
            return [{"id": attribute.getId(), "title": attribute.getTitle()}
                for attribute in attributes]

class ConferenceReviewingContributionsPerSelectedAttributeList(ListModificationBase, ConferenceReviewingPRMRefereeBase):
    #Note: don't change the order of the inheritance here!
    """ Class to return all the contributions ids for the selected track/session/type of the conference
    """

    def __init__(self, *params):
        ConferenceReviewingPRMRefereeBase.__init__(self, *params)

    def _checkParams(self):
        ConferenceReviewingPRMRefereeBase._checkParams(self)
        self._attribute = self._params.get("attribute", None)
        if self._attribute is None:
            raise ServiceError("ERR-REV5",_("No type/session/track specified"))
        self._selectedAttribute = self._params.get("selectedAttributes", None)
        if self._selectedAttribute is None:
            raise ServiceError("ERR-REV5",_("No attribute specified"))

    def _handleGet(self):
        contributionsPerSelectedAttribute = []
        for c in self._conf.getContributionList():
            for att in self._selectedAttribute:
                if self._attribute == 'type':
                    if c.getType() is not None and c.getId() not in contributionsPerSelectedAttribute:
                        if c.getType().getId() == att:
                            contributionsPerSelectedAttribute.append(c.getId())
                elif self._attribute == 'track':
                    if c.getTrack() is not None and c.getId() not in contributionsPerSelectedAttribute:
                        if c.getTrack().getId() == att:
                            contributionsPerSelectedAttribute.append(c.getId())
                elif self._attribute == 'session':
                    if c.getSession() is not None and c.getId() not in contributionsPerSelectedAttribute:
                        if c.getSession().getId() == att:
                            contributionsPerSelectedAttribute.append(c.getId())
                else:
                    raise ServiceError("ERR-REV5",_("No attribute specified"))

        return contributionsPerSelectedAttribute


class ConferenceReviewingUserCompetenceList(ListModificationBase, ConferenceReviewingPRMRefereeBase):
    #Note: don't change the order of the inheritance here!
    """ Class to return all the referees / editors / reviewers of the conference,
        plus their competences.
    """

    def __init__(self, *params):
        ConferenceReviewingPRMRefereeBase.__init__(self, *params)

    def _checkParams(self):
        ConferenceReviewingPRMRefereeBase._checkParams(self)
        self._role = self._params.get("role", None)
        if self._role is None:
            raise ServiceError("ERR-REV5",_("No role specified"))

    def _handleGet(self):
        return [{"id": user.getId(), "name": user.getStraightFullName(), "competences": c}
                for user, c in self._confPaperReview.getAllUserCompetences(True, self._role)]

class ConferenceReviewingAssignReferee(ConferenceReviewingAssignStaffBasePRM):
    """ Assigns a referee to a list of contributions
    """

    def _getAnswer(self):
        if self._confPaperReview.getChoice() == ConferencePaperReview.NO_REVIEWING or self._confPaperReview.getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
            raise ServiceError("ERR-REV6aa",_("can't assign referee"))
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
        if self._confPaperReview.getChoice() == ConferencePaperReview.NO_REVIEWING or self._confPaperReview.getChoice() == ConferencePaperReview.CONTENT_REVIEWING:
            raise ServiceError("ERR-REV6bb",_("can't assign layout reviewer"))
        if not self._targetUser:
            raise ServiceError("ERR-REV6b",_("user id not set"))

        for contribution in self._contributions:
            rm = contribution.getReviewManager()
            if rm.hasReferee() or self._confPaperReview.getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
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
        if self._confPaperReview.getChoice() == ConferencePaperReview.NO_REVIEWING or self._confPaperReview.getChoice() == ConferencePaperReview.LAYOUT_REVIEWING:
            raise ServiceError("ERR-REV6cc",_("can't assign content reviewer"))
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


######################################################
###  Assign/Remove Team classes ###
######################################################

class ConferenceReviewingAssignTeamPRM(ConferenceReviewingPRMBase, UserListModificationBase):
    """ Adds paper review managers to reviewers team for the conference
    """
    def _checkParams(self):
        UserListModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        for user in self._avatars:
            if not user in self._confPaperReview._paperReviewManagersList:
                self._confPaperReview.addPaperReviewManager(user)

        return True

class ConferenceReviewingRemoveTeamPRM(ConferenceReviewingPRMBase, UserModificationBase):
    """ Removes paper review manager from reviewers team for the conference
    """
    def _checkParams(self):
        UserModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        self._confPaperReview.removePaperReviewManager(self._targetUser)

        return True

class ConferenceReviewingAssignTeamReferee(ConferenceReviewingPRMBase, UserListModificationBase):
    """ Adds referee to reviewers team for the conference
    """
    def _checkParams(self):
        UserListModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        for user in self._avatars:
            if not user in self._confPaperReview._refereesList:
                self._confPaperReview.addReferee(user)

        return True

class ConferenceReviewingRemoveTeamReferee(ConferenceReviewingPRMBase, UserModificationBase):
    """ Removes referee from reviewers team for the conference
    """
    def _checkParams(self):
        UserModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        judgedContribs = self._confPaperReview.getJudgedContributions(self._targetUser)[:]
        for contribution in judgedContribs:
            rm = contribution.getReviewManager()
            if rm.hasReferee():
                rm.removeReferee()
        self._confPaperReview.removeReferee(self._targetUser)

        return True


class ConferenceReviewingAssignTeamEditor(ConferenceReviewingPRMBase, UserListModificationBase):
    """ Adds editor to reviewers team for the conference
    """
    def _checkParams(self):
        UserListModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        for user in self._avatars:
            if not user in self._confPaperReview._editorsList:
                self._confPaperReview.addEditor(user)

        return True

class ConferenceReviewingRemoveTeamEditor(ConferenceReviewingPRMBase, UserModificationBase):
    """ Removes editor from reviewers team for the conference
    """
    def _checkParams(self):
        UserModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        editedContribs = self._confPaperReview.getEditedContributions(self._targetUser)[:]
        for contribution in editedContribs:
            rm = contribution.getReviewManager()
            if rm.hasEditor():
                rm.removeEditor()
        self._confPaperReview.removeEditor(self._targetUser)

        return True


class ConferenceReviewingAssignTeamReviewer(ConferenceReviewingPRMBase, UserListModificationBase):
    """ Adds editor to reviewers team for the conference
    """
    def _checkParams(self):
        UserListModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        for user in self._avatars:
            if not user in self._confPaperReview._reviewersList:
                self._confPaperReview.addReviewer(user)

        return True

class ConferenceReviewingRemoveTeamReviewer(ConferenceReviewingPRMBase, UserModificationBase):
    """ Removes editor from reviewers team for the conference
    """
    def _checkParams(self):
        UserModificationBase._checkParams(self)
        ConferenceReviewingPRMBase._checkParams(self)

    def _checkProtection(self):
        ConferenceReviewingPRMBase._checkProtection(self)

    def _getAnswer(self):
        if not self._targetUser:
            raise ServiceError("ERR-REV6d",_("user id not set"))

        reviewedContribs = self._confPaperReview.getReviewedContributions(self._targetUser)[:]
        for contribution in reviewedContribs:
            rm = contribution.getReviewManager()
            rm.removeReviewer(self._targetUser)
        self._confPaperReview.removeReviewer(self._targetUser)

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
            raise ServiceError("ERR-REV7",_("Current kind of assessment not specified"))

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
            raise ServiceError("ERR-REV3c",_("Kind of deadline to change not set"))

    def _handleGet(self):
        lastReview = self._target.getReviewManager().getLastReview()
        if self._dueDateToChange == "Referee":
            date = lastReview.getAdjustedRefereeDueDate()
        elif self._dueDateToChange == "Editor":
            date = lastReview.getAdjustedEditorDueDate()
        elif self._dueDateToChange == "Reviewer":
            date = lastReview.getAdjustedReviewerDueDate()
        else:
            raise ServiceError("ERR-REV3d",_("Kind of deadline to change not set"))

        if date:
            return datetime.datetime.strftime(date,'%d/%m/%Y %H:%M')

class ContributionReviewingJudgementModification(ContributionReviewingTextModificationBase):

    def _handleSet(self):
        if self.getJudgementObject().isSubmitted():
            raise ServiceError("ERR-REV8a",_("You cannot modify an assessment marked as submitted"))
        self.getJudgementObject().setJudgement(self._value)

    def _handleGet(self):
        judgement = self.getJudgementObject().getJudgement()
        if judgement is None:
            return 'None'
        else:
            return judgement

class ContributionReviewingCommentsModification(ContributionReviewingHTMLModificationBase):

    def _handleSet(self):
        if self.getJudgementObject().isSubmitted():
            raise ServiceError("ERR-REV8b",_("You cannot modify an assessment marked as submitted"))
        self.getJudgementObject().setComments(self._value)

    def _handleGet(self):
        return self.getJudgementObject().getComments()

class ContributionReviewingCriteriaModification(ContributionReviewingTextModificationBase):

    def _checkParams(self):
        ContributionReviewingTextModificationBase._checkParams(self)
        self._criterion = self._params.get("criterion") # question id

    def _handleSet(self):
        if self.getJudgementObject().isSubmitted():
            raise ServiceError("ERR-REV8c",_("You cannot modify an assessment marked as submitted"))
        self.getJudgementObject().setAnswer(self._criterion, int(self._value), self._conf.getConfPaperReview().getNumberOfAnswers())

    def _handleGet(self):
        judgementObj = self.getJudgementObject()
        answer = judgementObj.getAnswer(self._criterion)
        if answer is None:
            answer = judgementObj.createAnswer(self._criterion)
        return answer.getRbValue()


class ContributionReviewingSetSubmitted(ContributionReviewingBase):

    def _getAnswer( self ):
        if self._params.has_key('value'):
            judgementObject = self.getJudgementObject()
            try:
                judgementObject.setSubmitted(not judgementObject.isSubmitted())
            except MaKaCError, e:
                raise ServiceError("ERR-REV9", e.getMessage())

            judgementObject.setAuthor(self._getUser())
            judgementObject.sendNotificationEmail(withdrawn = not judgementObject.isSubmitted())
        return self.getJudgementObject().isSubmitted()

class ContributionReviewingSubmitPaper(ContributionReviewingBase):

    def _checkProtection(self):
        if not self._target.canUserSubmit(self.getAW().getUser()):
            ContributionReviewingBase._checkProtection(self)

    def _getAnswer( self ):
        if len(self._target.getReviewing().getResourceList()) == 0:
            raise NoReportError(_("You need to attach a paper before submitting a revision."))
        self._target.getReviewManager().getLastReview().setAuthorSubmitted(True)
        return True

class ContributionReviewingCriteriaDisplay(ContributionReviewingBase):

    def _getAnswer( self ):
        return self.getJudgementObject().getAnswers()


#######################################
###  Paper reviewing question classes
#######################################

# Content questions
class PaperReviewingGetContentQuestions(ConferenceReviewingPRMBase):

    ''' Get the current list of content questions '''

    def _getAnswer(self):
        reviewingQuestions = self._confPaperReview.getReviewingQuestions()
        return fossilize(reviewingQuestions)


class PaperReviewingAddContentQuestion(ConferenceReviewingPRMBase):

    ''' Add a new question '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._value = self._params.get("value") # value is the question text

    def _getAnswer(self):
        self._confPaperReview.addReviewingQuestion(self._value)
        reviewingQuestions = self._confPaperReview.getReviewingQuestions()
        return fossilize(reviewingQuestions)


class PaperReviewingRemoveContentQuestion(ConferenceReviewingPRMBase):

    ''' Remove a question '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._value = self._params.get("value") # value is the question id

    def _getAnswer(self):
        # remove the question
        self._confPaperReview.removeReviewingQuestion(self._value)
        reviewingQuestions = self._confPaperReview.getReviewingQuestions()
        # Build the answer
        return fossilize(reviewingQuestions)


class PaperReviewingEditContentQuestion(ConferenceReviewingPRMBase):

    ''' Edit a question '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._id = self._params.get("id") # value is the question id
        self._text = self._params.get("text")

    def _getAnswer(self):
        # remove the question
        self._confPaperReview.editReviewingQuestion(self._id, self._text)
        reviewingQuestions = self._confPaperReview.getReviewingQuestions()
        # Build the answer
        return fossilize(reviewingQuestions)


# Layout questions
class PaperReviewingGetLayoutQuestions(ConferenceReviewingPRMBase):

    ''' Get the current list of Layout questions '''

    def _getAnswer(self):
        layoutQuestions = self._confPaperReview.getLayoutQuestions()
        return fossilize(layoutQuestions)


class PaperReviewingAddLayoutQuestion(ConferenceReviewingPRMBase):

    ''' Add a new question '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._value = self._params.get("value") # value is the question text

    def _getAnswer(self):
        self._confPaperReview.addLayoutQuestion(self._value)
        layoutQuestions = self._confPaperReview.getLayoutQuestions()
        return fossilize(layoutQuestions)


class PaperReviewingRemoveLayoutQuestion(ConferenceReviewingPRMBase):

    ''' Remove a question '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._value = self._params.get("value") # value is the question id

    def _getAnswer(self):
        # remove the question
        self._confPaperReview.removeLayoutQuestion(self._value)
        layoutQuestions = self._confPaperReview.getLayoutQuestions()
        # Build the answer
        return fossilize(layoutQuestions)


class PaperReviewingEditLayoutQuestion(ConferenceReviewingPRMBase):

    ''' Edit a question '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._id = self._params.get("id") # value is the question id
        self._text = self._params.get("text")

    def _getAnswer(self):
        # remove the question
        self._confPaperReview.editLayoutQuestion(self._id, self._text)
        layoutQuestions = self._confPaperReview.getLayoutQuestions()
        # Build the answer
        return fossilize(layoutQuestions)


# Status services
class PaperReviewingGetStatuses(ConferenceReviewingPRMBase):

    ''' Get the current list of Layout questions '''

    def _getAnswer(self):
        statuses = self._confPaperReview.getStatuses()
        return fossilize(statuses)

class PaperReviewingAddStatus(ConferenceReviewingPRMBase):

    ''' Add a new status '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._value = self._params.get("value") # value is the status name

    def _getAnswer(self):
        self._confPaperReview.addStatus(self._value, True)
        statuses = self._confPaperReview.getStatuses()
        return fossilize(statuses)


class PaperReviewingRemoveStatus(ConferenceReviewingPRMBase):

    ''' Remove a status '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._value = self._params.get("value") # value is the status id

    def _getAnswer(self):
        # remove the status
        self._confPaperReview.removeStatus(self._value)
        statuses = self._confPaperReview.getStatuses()
        # Build the answer
        return fossilize(statuses)


class PaperReviewingEditStatus(ConferenceReviewingPRMBase):

    ''' Edit a status '''

    def _checkParams(self):
        ConferenceReviewingPRMBase._checkParams(self)
        self._id = self._params.get("id") # value is the status id
        self._name = self._params.get("text")

    def _getAnswer(self):
        # remove the status
        self._confPaperReview.editStatus(self._id, self._name)
        statuses = self._confPaperReview.getStatuses()
        # Build the answer
        return fossilize(statuses)




methodMap = {
    "conference.changeReviewingMode": ConferenceReviewingModeModification,
    "conference.deleteTemplate" : ConferenceReviewingDeleteTemplate,
    "conference.changeCompetences": ConferenceReviewingCompetenceModification,
    "conference.changeDefaultDueDate" : ConferenceReviewingDefaultDueDateModification,
    "conference.attributeList" : ConferenceReviewingContributionsAttributeList,
    "conference.contributionsIdPerSelectedAttribute" : ConferenceReviewingContributionsPerSelectedAttributeList,
    "conference.userCompetencesList": ConferenceReviewingUserCompetenceList,

    "conference.assignReferee" : ConferenceReviewingAssignReferee,
    "conference.removeReferee" : ConferenceReviewingRemoveReferee,
    "conference.assignEditor" : ConferenceReviewingAssignEditor,
    "conference.removeEditor" : ConferenceReviewingRemoveEditor,
    "conference.addReviewer" : ConferenceReviewingAddReviewer,
    "conference.removeReviewer" : ConferenceReviewingRemoveReviewer,
    "conference.removeAllReviewers" : ConferenceReviewingRemoveAllReviewers,

    "conference.PRMEmailNotif" : ConferenceReviewingAutoEmailsModificationPRM,
    "conference.RefereeEmailNotif" : ConferenceReviewingAutoEmailsModificationReferee,
    "conference.EditorEmailNotif" : ConferenceReviewingAutoEmailsModificationEditor,
    "conference.ReviewerEmailNotif" : ConferenceReviewingAutoEmailsModificationReviewer,
    "conference.RefereeEmailNotifForContribution" : ConferenceReviewingAutoEmailsModificationRefereeForContribution,
    "conference.EditorEmailNotifForContribution" : ConferenceReviewingAutoEmailsModificationEditorForContribution,
    "conference.ReviewerEmailNotifForContribution" : ConferenceReviewingAutoEmailsModificationReviewerForContribution,
    "conference.RefereeEmailJudgementNotif" : ConferenceReviewingAutoEmailsModificationRefereeJudgement,
    "conference.EditorEmailJudgementNotif" : ConferenceReviewingAutoEmailsModificationEditorJudgement,
    "conference.ReviewerEmailJudgementNotif" : ConferenceReviewingAutoEmailsModificationReviewerJudgement,
    "conference.AuthorSubmittedMatRefereeNotif" : ConferenceReviewingAutoEmailsModificationAuthorSubmittedMatReferee,
    "conference.AuthorSubmittedMatEditorNotif" : ConferenceReviewingAutoEmailsModificationAuthorSubmittedMatEditor,
    "conference.AuthorSubmittedMatReviewerNotif" : ConferenceReviewingAutoEmailsModificationAuthorSubmittedMatReviewer,
    "conference.EditorSubmittedRefereeNotif" : ConferenceReviewingAutoEmailsModificationEditorSubmittedReferee,
    "conference.ReviewerSubmittedRefereeNotif" : ConferenceReviewingAutoEmailsModificationReviewerSubmittedReferee,


    "conference.assignTeamPRM" : ConferenceReviewingAssignTeamPRM,
    "conference.removeTeamPRM" : ConferenceReviewingRemoveTeamPRM,
    "conference.assignTeamReferee" : ConferenceReviewingAssignTeamReferee,
    "conference.removeTeamReferee" : ConferenceReviewingRemoveTeamReferee,
    "conference.assignTeamEditor" : ConferenceReviewingAssignTeamEditor,
    "conference.removeTeamEditor" : ConferenceReviewingRemoveTeamEditor,
    "conference.assignTeamReviewer" : ConferenceReviewingAssignTeamReviewer,
    "conference.removeTeamReviewer" : ConferenceReviewingRemoveTeamReviewer,

    "contribution.changeDueDate": ContributionReviewingDueDateModification,
    "contribution.changeComments": ContributionReviewingCommentsModification,
    "contribution.changeJudgement": ContributionReviewingJudgementModification,
    "contribution.changeCriteria": ContributionReviewingCriteriaModification,
    "contribution.getCriteria": ContributionReviewingCriteriaDisplay,
    "contribution.setSubmitted": ContributionReviewingSetSubmitted,
    "contribution.submitPaper": ContributionReviewingSubmitPaper,

    "paperReviewing.getContentQuestions": PaperReviewingGetContentQuestions,
    "paperReviewing.addContentQuestion": PaperReviewingAddContentQuestion,
    "paperReviewing.removeContentQuestion": PaperReviewingRemoveContentQuestion,
    "paperReviewing.editContentQuestion": PaperReviewingEditContentQuestion,

    "paperReviewing.getLayoutQuestions": PaperReviewingGetLayoutQuestions,
    "paperReviewing.addLayoutQuestion": PaperReviewingAddLayoutQuestion,
    "paperReviewing.removeLayoutQuestion": PaperReviewingRemoveLayoutQuestion,
    "paperReviewing.editLayoutQuestion": PaperReviewingEditLayoutQuestion,

    "paperReviewing.getStatuses": PaperReviewingGetStatuses,
    "paperReviewing.addStatus": PaperReviewingAddStatus,
    "paperReviewing.removeStatus": PaperReviewingRemoveStatus,
    "paperReviewing.editStatus": PaperReviewingEditStatus
    }
