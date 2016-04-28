# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.services.implementation.base import ParameterManager

from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError, NoReportError

from MaKaC.common.search import make_participation_from_obj

import MaKaC.conference as conference
from MaKaC.common.fossilize import fossilize
from MaKaC.user import AvatarHolder
import MaKaC.webinterface.pages.contributionReviewing as contributionReviewing
import MaKaC.domain as domain
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.user import principal_from_fossil


class ContributionBase(object):

    def _checkParams( self ):
        try:
            self._target = self._conf = conference.ConferenceHolder().getById(self._params["conference"]);
        except:
            try:
                self._target = self._conf = conference.ConferenceHolder().getById(self._params["confId"]);
            except:
                raise ServiceError("ERR-E4", "Invalid conference id.")

        if self._conf == None:
            raise Exception("Conference id not specified.")

        contrib_id = int(self._params.get('contribId', self._params.get('contribution')))
        self._target = self._contribution = self.contrib = Contribution.get_one(contrib_id)

        # create a parameter manager that checks the consistency of passed parameters
        self._pm = ParameterManager(self._params)

class ContributionDisplayBase(ProtectedDisplayService, ContributionBase):

    def _checkParams(self):
        ContributionBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)

class ContributionModifBase(ProtectedModificationService, ContributionBase):

    def _checkParams(self):
        ContributionBase._checkParams(self)
        ProtectedModificationService._checkParams(self)

    def _checkProtection(self):
        if self._target.getSession() != None:
            if self._target.getSession().canCoordinate(self.getAW(), "modifContribs"):
                return
        ProtectedModificationService._checkProtection(self)


class ContributionProtectionUserList(ContributionModifBase):

    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._contribution.getAllowedToAccessList())


class ContributionProtectionAddUsers(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        self._principals = [principal_from_fossil(f, allow_pending=True) for f in self._params['value']]
        self._user = self.getAW().getUser()

    def _getAnswer(self):
        for principal in self._principals:
            self._contribution.grantAccess(principal)
        return fossilize(self._contribution.getAccessController().getAccessList())

class ContributionProtectionRemoveUser(ContributionModifBase):
    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        self._principal = principal_from_fossil(self._params['value'], allow_missing_groups=True)
        self._user = self.getAW().getUser()

    def _getAnswer(self):
        self._contribution.revokeAccess(self._principal)


class ContributionGetChildrenProtected(ContributionModifBase):

    def _getAnswer(self):
        return fossilize(self._contribution.getAccessController().getProtectedChildren())

class ContributionGetChildrenPublic(ContributionModifBase):

    def _getAnswer(self):
        return fossilize(self._contribution.getAccessController().getPublicChildren())

class ContributionParticipantsBase(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        self._pm = ParameterManager(self._params)
        self._kindOfList = self._pm.extract("kindOfList", pType=str, allowEmpty=False)

    def _isEmailAlreadyUsed(self, email):
        participantList = []
        if self._kindOfList in ("prAuthor", "coAuthor"):
            participantList = self._contribution.getPrimaryAuthorList() + self._contribution.getCoAuthorList()
        elif self._kindOfList == "speaker":
            participantList = self._contribution.getSpeakerList()

        for part in participantList:
            if email == part.getEmail():
                return True
        return False

    def _getParticipantsList(self, participantList):
        result = []
        for part in participantList:
            partFossil = fossilize(part)
            # var to control if we have to show the entry in the author menu to allow add submission rights
            isSubmitter = False
            av = AvatarHolder().match({"email": part.getEmail()}, searchInAuthenticators=False, exact=True)
            if not av:
                if part.getEmail() in self._contribution.getSubmitterEmailList():
                    isSubmitter = True
            elif (av[0] in self._contribution.getSubmitterList() or self._conf.getPendingQueuesMgr().isPendingSubmitter(part)):
                isSubmitter = True
            partFossil["showSubmitterCB"] = not isSubmitter
            result.append(partFossil)
        return result



class ContributionParticipantsUserBase(ContributionParticipantsBase):

    def _checkParams(self):
        ContributionParticipantsBase._checkParams(self)
        if self._kindOfList == "speaker":
            self._participant = self._contribution.getSpeakerById(self._pm.extract("userId", pType=str, allowEmpty=False))
        else:
            self._participant = self._contribution.getAuthorById(self._pm.extract("userId", pType=str, allowEmpty=False))
        if self._participant == None:
            raise ServiceAccessError(_("The user that you are trying to delete does not exist."))


class ContributionAddExistingParticipant(ContributionParticipantsBase):

    def _checkParams(self):
        ContributionParticipantsBase._checkParams(self)
        self._submissionRights = self._pm.extract("presenter-grant-submission", pType=bool, allowEmpty=False)
        self._userList = self._pm.extract("userList", pType=list, allowEmpty=False)
        # Check if there is already a user with the same email
        for user in self._userList:
            if self._isEmailAlreadyUsed(user["email"]):
                if self._kindOfList == "speaker":
                    raise ServiceAccessError(_("The email address %s (belonging to a user you are adding) is already used by another speaker in the current speaker list. Speaker(s) not added.") % user["email"])
                else:
                    raise ServiceAccessError(_("The email address %s (belonging to a user you are adding) is already used by another author in the list of primary authors or co-authors. Author(s) not added.") % user["email"])

    def _newParticipant(self, a):
        part = make_participation_from_obj(a)
        if self._kindOfList == "prAuthor":
            self._contribution.addPrimaryAuthor(part)
        elif self._kindOfList == "coAuthor":
            self._contribution.addCoAuthor(part)
        elif self._kindOfList == "speaker":
            self._contribution.newSpeaker(part)
        return part

    def _getAnswer(self):
        for user in self._userList:
            if user["_type"] == "Avatar":  # new speaker
                part = self._newParticipant(principal_from_fossil(user, allow_pending=True))
            elif user["_type"] == "ContributionParticipation":  # adding existing author to speaker
                author_index_author_id = "{familyName} {firstName} {email}".format(**user).lower()
                author = self._conf.getAuthorIndex().getById(author_index_author_id)[0]
                part = self._newParticipant(author)
            if self._submissionRights and part:
                self._contribution.grantSubmission(part)
        if self._kindOfList == "prAuthor":
            return self._getParticipantsList(self._contribution.getPrimaryAuthorList())
        elif self._kindOfList == "coAuthor":
            return self._getParticipantsList(self._contribution.getCoAuthorList())
        elif self._kindOfList == "speaker":
            return self._getParticipantsList(self._contribution.getSpeakerList())
        else:
            raise ServiceError("ERR-UK0", _("Invalid kind of list of users."))


class ContributionAddNewParticipant(ContributionParticipantsBase):

    def _checkParams(self):
        ContributionParticipantsBase._checkParams(self)
        self._userData = self._pm.extract("userData", pType=dict, allowEmpty=False)
        email = self._userData.get("email", "")
        if email != "" and self._isEmailAlreadyUsed(email):
            raise ServiceAccessError(_("The email address is already used by another %s. %s not added.") % (self._kindOfList, self._kindOfList))

    def _newParticipant(self):
        part = conference.ContributionParticipation()
        part.setTitle(self._userData.get("title", ""))
        part.setFirstName(self._userData.get("firstName", ""))
        part.setFamilyName(self._userData.get("familyName", ""))
        part.setAffiliation(self._userData.get("affiliation", ""))
        part.setEmail(self._userData.get("email", ""))
        part.setAddress(self._userData.get("address", ""))
        part.setPhone(self._userData.get("phone", ""))
        part.setFax(self._userData.get("fax", ""))
        if self._kindOfList == "prAuthor":
            self._contribution.addPrimaryAuthor(part)
        elif self._kindOfList == "coAuthor":
            self._contribution.addCoAuthor(part)
        elif self._kindOfList == "speaker":
            self._contribution.newSpeaker(part)
        #If the participant needs to be given submission rights
        if self._userData.get("submission", False):
            if self._userData.get("email", "") == "":
                raise ServiceAccessError(_("It is necessary to enter the email of the %s if you want to add him as submitter.") % self._kindOfList)
            self._contribution.grantSubmission(part)

    def _getAnswer(self):
        self._newParticipant()
        if self._kindOfList == "prAuthor":
            return self._getParticipantsList(self._contribution.getPrimaryAuthorList())
        elif self._kindOfList == "coAuthor":
            return self._getParticipantsList(self._contribution.getCoAuthorList())
        elif self._kindOfList == "speaker":
            return self._getParticipantsList(self._contribution.getSpeakerList())
        else:
            raise ServiceError("ERR-UK0", _("Invalid kind of list of users."))


class ContributionRemoveParticipant(ContributionParticipantsUserBase):

    def _getAnswer(self):
        if self._kindOfList == "prAuthor":
            self._contribution.removePrimaryAuthor(self._participant, removeSpeaker=0)
            #return [self._getParticipantsList(self._contribution.getPrimaryAuthorList()), self._getParticipantsList(self._contribution.getSpeakerList())]
            return self._getParticipantsList(self._contribution.getPrimaryAuthorList())
        elif self._kindOfList == "coAuthor":
            self._contribution.removeCoAuthor(self._participant, removeSpeaker=0)
            #return [self._getParticipantsList(self._contribution.getCoAuthorList()), self._getParticipantsList(self._contribution.getSpeakerList())]
            return self._getParticipantsList(self._contribution.getCoAuthorList())
        elif self._kindOfList == "speaker":
            self._contribution.removeSpeaker(self._participant)
            return self._getParticipantsList(self._contribution.getSpeakerList())
        else:
            raise ServiceError("ERR-UK0", _("Invalid kind of list of users."))


class ContributionEditParticipantData(ContributionParticipantsBase):

    def _checkParams(self):
        ContributionParticipantsBase._checkParams(self)
        self._userData = self._pm.extract("userData", pType=dict, allowEmpty=False)
        self._userId = self._pm.extract("userId", pType=str, allowEmpty=False)
        if (self._kindOfList == "speaker"):
            self._participant = self._contribution.getSpeakerById(self._pm.extract("userId", pType=str, allowEmpty=False))
        else:
            self._participant = self._contribution.getAuthorById(self._pm.extract("userId", pType=str, allowEmpty=False))
        if self._participant == None:
            raise ServiceError("ERR-U0", _("User does not exist."))
        if self._userData.get("email", "") != "" and self._isEmailAlreadyUsed():
            raise ServiceAccessError(_("The email address is already used by another participant. Participant not modified."))
        #self._eventType = self._pm.extract("eventType", pType=str, allowEmpty=False)

    def _isEmailAlreadyUsed(self):
        participantList = []
        if self._kindOfList in ("prAuthor", "coAuthor"):
            participantList = self._contribution.getPrimaryAuthorList() + self._contribution.getCoAuthorList()
        elif self._kindOfList == "speaker":
            participantList = self._contribution.getSpeakerList()
        for auth in participantList:
            # check if the email is already used by other different author
            if self._userData.get("email", "") == auth.getEmail() and self._userId != str(auth.getId()):
                return True
        return False

    def _editParticipant(self):
        self._participant.setTitle(self._userData.get("title", ""))
        self._participant.setFirstName(self._userData.get("firstName", ""))
        self._participant.setFamilyName(self._userData.get("familyName", ""))
        self._participant.setAffiliation(self._userData.get("affiliation", ""))
        self._participant.setAddress(self._userData.get("address", ""))
        self._participant.setPhone(self._userData.get("phone", ""))
        self._participant.setFax(self._userData.get("fax", ""))

        grantSubm = False
        if self._participant.getEmail().lower().strip() != self._userData.get("email", "").lower().strip():
            #----If it's already in the pending queue in order to grant
            #    submission rights we must unindex and after the modification of the email,
            #    index again...
            if self._conf.getPendingQueuesMgr().isPendingSubmitter(self._participant):
                self._conf.getPendingQueuesMgr().removePendingSubmitter(self._participant)
                grantSubm = True
            #-----
        self._participant.setEmail(self._userData.get("email", ""))
        #If the author needs to be given submission rights because the checkbox is selected
        if self._userData.get("submission", False):
            if self._userData.get("email", "") == "":
                raise ServiceAccessError(_("It is necessary to enter the email of the user if you want to add him as submitter."))
            grantSubm = True
        if grantSubm:
            self._contribution.grantSubmission(self._participant)

    def _getAnswer(self):
        self._editParticipant()
        if self._kindOfList == "prAuthor":
            return self._getParticipantsList(self._contribution.getPrimaryAuthorList())
        elif self._kindOfList == "coAuthor":
            return self._getParticipantsList(self._contribution.getCoAuthorList())
        elif self._kindOfList == "speaker":
            return self._getParticipantsList(self._contribution.getSpeakerList())
        else:
            raise ServiceError("ERR-UK0", _("Invalid kind of list of users."))


class ContributionSendEmailData(ContributionParticipantsUserBase):

    def _getAnswer(self):
        return {"confTitle": self._conf.getTitle(),
                "contribTitle": self._contribution.getTitle(),
                "contribId": str(self._contribution.getId()),
                "email": self._participant.getEmail()
                }


class ContributionChangeSubmissionRights(ContributionParticipantsUserBase):

    def _checkParams(self):
        ContributionParticipantsUserBase._checkParams(self)
        if self._participant.getEmail() == "":
            raise ServiceAccessError(_("It is not possible to grant submission rights to a participant without an email address. Please edit participant details and set an email address."))
        self._action = self._pm.extract("action", pType=str, allowEmpty=False)
        self._eventType = self._pm.extract("eventType", pType=str, allowEmpty=False)

    def _getAnswer(self):
        if self._action == "grant":
            self._contribution.grantSubmission(self._participant)
        elif self._action == "remove":
            av = AvatarHolder().match({"email": self._participant.getEmail()}, exact=True, searchInAuthenticators=False)
            if not av:
                self._contribution.revokeSubmissionEmail(self._participant.getEmail())
            else:
                self._contribution.revokeSubmission(av[0])
        if self._eventType == "conference":
            return [self._getParticipantsList(self._contribution.getPrimaryAuthorList()),
                    self._getParticipantsList(self._contribution.getCoAuthorList()),
                    self._getParticipantsList(self._contribution.getSpeakerList())]
        else:
            return self._getParticipantsList(self._contribution.getSpeakerList())

class ContributionUpdateAuthorList(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        self._from= self._pm.extract("from", pType=str, allowEmpty=False)
        self._to= self._pm.extract("to", pType=str, allowEmpty=False)
        self._item = self._pm.extract("item", pType=str, allowEmpty=False)
        self._index = self._pm.extract("index", pType=int, allowEmpty=False)


    def _getAnswer(self):

        getAuthor = {'inPlacePrimaryAuthors': self._contribution.getPrimaryAuthorById,
                   'inPlaceCoAuthors': self._contribution.getCoAuthorById,
                   'inPlaceSpeakers': self._contribution.getSpeakerById}
        addAuthor = {'inPlacePrimaryAuthors': self._contribution.addPrimaryAuthor,
                   'inPlaceCoAuthors': self._contribution.addCoAuthor,
                   'inPlaceSpeakers': self._contribution.addSpeaker}
        remAuthor = {'inPlacePrimaryAuthors': self._contribution.removePrimaryAuthor,
                   'inPlaceCoAuthors': self._contribution.removeCoAuthor}

        author = getAuthor[self._from](self._item)

        if self._to != 'inPlaceSpeakers' and self._from != 'inPlaceSpeakers':
            remAuthor[self._from](author, removeSpeaker=0)

        addAuthor[self._to](author, index=self._index)
# IF we want to update all the lists (to update the possible repeated authors (e.g. in speakers list)
#        if self._contribution.getConference().getType() == "conference":
#            return [self._getParticipantsList(self._contribution.getPrimaryAuthorList()),
#                    self._getParticipantsList(self._contribution.getCoAuthorList()),
#                    self._getParticipantsList(self._contribution.getSpeakerList())]
#        else:
#            return self._getParticipantsList(self._contribution.getSpeakerList())
        return True


class ContributionReorderAuthorList(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        self._list= self._pm.extract("list", pType=str, allowEmpty=False)
        self._item = self._pm.extract("item", pType=str, allowEmpty=False)
        self._index = self._pm.extract("index", pType=int, allowEmpty=False)


    def _getAnswer(self):
        changePos = {'inPlacePrimaryAuthors': self._contribution.changePosPrimaryAuthor,
                   'inPlaceCoAuthors': self._contribution.changePosCoAuthor,
                   'inPlaceSpeakers': self._contribution.changePosSpeaker}
        getAuthor = {'inPlacePrimaryAuthors': self._contribution.getPrimaryAuthorById,
                   'inPlaceCoAuthors': self._contribution.getCoAuthorById,
                   'inPlaceSpeakers': self._contribution.getSpeakerById}

        author = getAuthor[self._list](self._item)
        changePos[self._list](author, self._index)

        return True


class ContributionSubmittersBase(ContributionModifBase):

    def _checkParams(self):
        ContributionModifBase._checkParams(self)
        self._pm = ParameterManager(self._params)

    def _removeUserFromSubmitterList(self, submitterId):
        for submitter in self._contribution.getSubmitterList():
            if submitter.getId() == submitterId:
                self._contribution.revokeSubmission(submitter)
                return True
        return False

    def _getSubmittersList(self):
        result = []
        for submitter in self._contribution.getSubmitterList():
            submitterFossil = fossilize(submitter)
            if isinstance(submitter, AvatarUserWrapper):
                isSpeaker = False
                if self._conf.getType() == "conference":
                    isPrAuthor = False
                    isCoAuthor = False
                    if self._contribution.isPrimaryAuthorByEmail(submitter.getEmail()):
                        isPrAuthor = True
                    if self._contribution.isCoAuthorByEmail(submitter.getEmail()):
                        isCoAuthor = True
                    submitterFossil["isPrAuthor"] = isPrAuthor
                    submitterFossil["isCoAuthor"] = isCoAuthor
                if self._contribution.isSpeakerByEmail(submitter.getEmail()):
                    isSpeaker = True
                submitterFossil["isSpeaker"] = isSpeaker
            result.append(submitterFossil)
        # get pending users
        for email in self._contribution.getSubmitterEmailList():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result


class ContributionAddExistingSubmitter(ContributionSubmittersBase):

    def _checkParams(self):
        ContributionSubmittersBase._checkParams(self)
        self._principals = [principal_from_fossil(f, allow_pending=True)
                            for f in self._pm.extract("userList", pType=list, allowEmpty=False)]

    def _getAnswer(self):
        for principal in self._principals:
            self._contribution.grantSubmission(principal)
        return self._getSubmittersList()


class ContributionRemoveSubmitter(ContributionSubmittersBase):

    def _checkParams(self):
        ContributionSubmittersBase._checkParams(self)
        self._submitterId = self._pm.extract("userId", pType=str, allowEmpty=False)
        self._kindOfUser = self._pm.extract("kindOfUser", pType=str, allowEmpty=True, defaultValue=None)

    def _getAnswer(self):
        if self._kindOfUser == "pending":
            # remove pending email, self._submitterId is an email address
            self._contribution.revokeSubmissionEmail(self._submitterId)
        else:
            try:
                principal = principal_from_fossil(self._params['principal'], allow_missing_groups=True)
            except ValueError:
                # WTF is this.. this used to be called if the user wasn't in avatarholder
                self._removeUserFromSubmitterList(self._submitterId)
            else:
                self._contribution.revokeSubmission(principal)
        return self._getSubmittersList()


class ContributionSumissionControlModifyUserRol(ContributionSubmittersBase):

    def _checkParams(self):
        ContributionSubmittersBase._checkParams(self)
        self._submitterId = self._pm.extract("userId", pType=str, allowEmpty=False)
        self._kindOfList = self._pm.extract("kindOfList", pType=str, allowEmpty=False)


class ContributionSumissionControlAddAsAuthor(ContributionSumissionControlModifyUserRol):

    def _newParticipant(self, a):
        part = conference.ContributionParticipation()
        part.setTitle(a.getTitle())
        part.setFirstName(a.getName())
        part.setFamilyName(a.getSurName())
        part.setAffiliation(a.getOrganisation())
        part.setEmail(a.getEmail())
        part.setAddress(a.getAddress())
        part.setPhone(a.getTelephone())
        part.setFax(a.getFax())
        if self._kindOfList == "prAuthor":
            self._contribution.addPrimaryAuthor(part)
        elif self._kindOfList == "coAuthor":
            self._contribution.addCoAuthor(part)
        elif self._kindOfList == "speaker":
            self._contribution.newSpeaker(part)

    def _getAnswer(self):
        av = AvatarHolder().getById(self._submitterId)
        if av is None:
            raise NoReportError(_("It seems this user has been removed from the database or has been merged into another. Please remove it and add it again."))
        self._newParticipant(av)
        return self._getSubmittersList()


class ContributionSumissionControlRemoveAsAuthor(ContributionSumissionControlModifyUserRol):

    def _getParticipantByEmail(self, email):
        if self._kindOfList == "prAuthor":
            for prAuthor in self._contribution.getPrimaryAuthorList():
                if prAuthor.getEmail() == email:
                    return prAuthor
        elif self._kindOfList == "coAuthor":
            for coAuthor in self._contribution.getCoAuthorList():
                if coAuthor.getEmail() == email:
                    return coAuthor
        elif self._kindOfList == "speaker":
            for speaker in self._contribution.getSpeakerList():
                if speaker.getEmail() == email:
                    return speaker
        else:
            raise ServiceError("ERR-UK0", _("Invalid kind of list of users."))
        # user not found
        raise ServiceError("ERR-USC", _("User not found in the list."))


    def _getAnswer(self):
        av = AvatarHolder().getById(self._submitterId)
        if av is None:
            raise NoReportError(_("It seems this user has been removed from the database or has been merged into another. Please remove it and add it again."))
        participant = self._getParticipantByEmail(av.getEmail())
        if self._kindOfList == "prAuthor":
            self._contribution.removePrimaryAuthor(participant, removeSpeaker=0)
        elif self._kindOfList == "coAuthor":
            self._contribution.removeCoAuthor(participant, removeSpeaker=0)
        elif self._kindOfList == "speaker":
            self._contribution.removeSpeaker(participant)

        return self._getSubmittersList()


class ContributionManagerListBase(ContributionModifBase):

    def _getManagersList(self):
        result = fossilize(self._contribution.getManagerList())
        # get pending users
        for email in self._contribution.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result


class ContributionAddExistingManager(ContributionManagerListBase):

    def _checkParams(self):
        ContributionManagerListBase._checkParams(self)
        self._principals = [principal_from_fossil(f, allow_pending=True)
                            for f in self._pm.extract("userList", pType=list, allowEmpty=False)]

    def _getAnswer(self):
        for principal in self._principals:
            self._contribution.grantModification(principal)
        return self._getManagersList()


class ContributionRemoveManager(ContributionManagerListBase):

    def _checkParams(self):
        ContributionManagerListBase._checkParams(self)
        self._principal = principal_from_fossil(self._params['principal'], allow_missing_groups=True)

    def _getAnswer(self):
        self._contribution.revokeModification(self._principal)
        return self._getManagersList()


class ContributionReviewHistory(ContributionDisplayBase):

    def _getAnswer(self):
        return contributionReviewing.WContributionReviewingHistory(self._contribution).getHTML({"ShowReviewingTeam" : False})


class ContributionProtectionToggleDomains(ContributionModifBase):

    def _checkParams(self):
        self._params['contribId'] = self._params['targetId']
        ContributionModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._domainId = pm.extract("domainId", pType=str)
        self._add = pm.extract("add", pType=bool)

    def _getAnswer(self):
        dh = domain.DomainHolder()
        d = dh.getById(self._domainId)
        if self._add:
            self._target.requireDomain(d)
        elif not self._add:
            self._target.freeDomain(d)


methodMap = {
    "protection.getAllowedUsersList": ContributionProtectionUserList,
    "protection.addAllowedUsers": ContributionProtectionAddUsers,
    "protection.removeAllowedUser": ContributionProtectionRemoveUser,
    "protection.getProtectedChildren": ContributionGetChildrenProtected,
    "protection.getPublicChildren": ContributionGetChildrenPublic,

    "participants.addNewParticipant": ContributionAddNewParticipant,
    "participants.addExistingParticipant": ContributionAddExistingParticipant,
    "participants.editParticipantData": ContributionEditParticipantData,
    "participants.removeParticipant": ContributionRemoveParticipant,
    "participants.sendEmailData": ContributionSendEmailData,
    "participants.changeSubmissionRights": ContributionChangeSubmissionRights,
    "participants.updateAuthorList": ContributionUpdateAuthorList,
    "participants.reorderAuthorList": ContributionReorderAuthorList,

    "protection.submissionControl.addExistingSubmitter": ContributionAddExistingSubmitter,
    "protection.submissionControl.removeSubmitter": ContributionRemoveSubmitter,
    "protection.submissionControl.addAsAuthor": ContributionSumissionControlAddAsAuthor,
    "protection.submissionControl.removeAsAuthor": ContributionSumissionControlRemoveAsAuthor,

    "protection.toggleDomains": ContributionProtectionToggleDomains,
    "protection.addExistingManager": ContributionAddExistingManager,
    "protection.removeManager": ContributionRemoveManager,
    "review.getReviewHistory": ContributionReviewHistory
}
