# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.conference import ConferenceModifBase
import MaKaC.user as user
from MaKaC.common.fossilize import fossilize
from MaKaC.user import AvatarHolder
from MaKaC.services.interface.rpc.common import ServiceError, NoReportError


class ChangeAbstractSubmitter(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        submitterId = pm.extract("submitterId", pType=str, allowEmpty=False)
        abstractId = pm.extract("abstractId", pType=str, allowEmpty=False)
        self._abstract = self._conf.getAbstractMgr().getAbstractById(abstractId)
        self._submitter = user.AvatarHolder().getById(submitterId)
        if self._submitter is None:
            raise NoReportError(_("The user that you are changing does not exist anymore in the database"))


    def _getAnswer(self):
        self._abstract.setSubmitter(self._submitter)
        return {"name": self._submitter.getFullName(),
                "affiliation": self._submitter.getAffiliation(),
                "email": self._submitter.getEmail()}


class AddLateSubmissionAuthUser(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        ah = AvatarHolder()
        for user in self._userList:
            if user["id"] != None:
                self._conf.getAbstractMgr().addAuthorizedSubmitter(ah.getById(user["id"]))
            else:
                raise ServiceError("ERR-U0", _("User does not exist."))
        return fossilize(self._conf.getAbstractMgr().getAuthorizedSubmitterList())


class RemoveLateSubmissionAuthUser(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        ah = AvatarHolder()
        userId = pm.extract("userId", pType=str, allowEmpty=False)
        self._user = ah.getById(userId)
        if self._user == None:
            raise ServiceError("ERR-U0", _("User '%s' does not exist.") % userId)

    def _getAnswer(self):
        self._conf.getAbstractMgr().removeAuthorizedSubmitter(self._user)
        return fossilize(self._conf.getAbstractMgr().getAuthorizedSubmitterList())


class AddField(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self.fieldId = pm.extract("id", pType=str, allowEmpty=True)
        self.name = pm.extract("name", pType=str, allowEmpty=False)
        self.caption = pm.extract("caption", pType=str, allowEmpty=False)
        self.maxLength = pm.extract("maxLength", pType=int, allowEmpty=True, defaultValue=0)
        self.isMandatory = pm.extract("isMandatory", pType=bool, allowEmpty=False)
        self.fieldType = pm.extract("fieldType", pType=str, allowEmpty=False)
        self.fieldLimitation = pm.extract("fieldLimitation", pType=str, allowEmpty=False)

    def _getAnswer(self):
        self._conf.getAbstractMgr().addAbstractField(self.fieldId, self.name, self.caption,
                                                     self.maxLength, self.isMandatory,
                                                     self.fieldType, self.fieldLimitation)


class GetField(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self.fieldId = pm.extract("id", pType=str, allowEmpty=False)

    def _getAnswer(self):
        field = self._conf.getAbstractMgr().getAbstractFieldsMgr().getFieldById(self.fieldId)
        if field is None:
            raise ServiceError("ERR-U0", _("Field '%s' does not exist for this conference.") % self.fieldId)
        return fossilize(field)


methodMap = {
    "changeSubmitter": ChangeAbstractSubmitter,
    "lateSubmission.addExistingLateAuthUser": AddLateSubmissionAuthUser,
    "lateSubmission.removeLateAuthUser": RemoveLateSubmissionAuthUser,
    "fields.addField": AddField,
    "fields.getField": GetField
}
