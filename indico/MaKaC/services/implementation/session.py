# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

"""
Session-related services
"""

from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError
from MaKaC.services.implementation import conference as conferenceServices
import MaKaC.webinterface.locators as locators
from MaKaC.conference import SessionSlot, SessionChair
from MaKaC.common.fossilize import fossilize
from MaKaC.user import AvatarHolder
import MaKaC.domain as domain
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.user import principal_from_fossil


class SessionBase(conferenceServices.ConferenceBase):

    def _checkParams( self ):

        try:
            conferenceServices.ConferenceBase._checkParams(self)

            l = locators.WebLocator()
            l.setSession( self._params )
            self._session = self._target = l.getObject()
            self._conf = self._session.getConference()

#        self._conf = self._target
#
#        try:
#            self._session = self._target = self._conf.getSessionById(self._params["session"])
#            if self._target == None:
#                raise ServiceError("ERR-S4", "Invalid session id.")
#        except:
#            raise ServiceError("ERR-S4", "Invalid session id.")
        except Exception, e:
            raise ServiceError("ERR-S4", "Invalid session id.")

class SessionModifBase(SessionBase, ProtectedModificationService):

    def _checkParams( self ):
        SessionBase._checkParams(self)
        if self._params.has_key("scheduleEntry"):
            if self._params.get("sessionTimetable", False):
                self._schEntry = self._session.getSchedule().getEntryById(self._params["scheduleEntry"])
            else:
                self._schEntry = self._conf.getSchedule().getEntryById(self._params["scheduleEntry"])
            if self._schEntry == None:
                raise ServiceError("ERR-E4", "Invalid scheduleEntry id.")
            elif isinstance(self._schEntry.getOwner(), SessionSlot):
                self._slot = self._schEntry.getOwner()

    def _checkProtection(self):
        if self._session.isClosed():
            raise ServiceAccessError(_(""""The modification of the session "%s" is not allowed because it is closed""")%self._session.getTitle())
        ProtectedModificationService._checkProtection(self)

    def _getCheckFlag(self):

        aw = self.getAW()

        if self._session.canModify(aw):
            # automatically adapt everything
            return 2
        elif self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
            return 2
        else:
            return 1

class SessionModifCoordinationBase(SessionModifBase):

    def _checkProtection(self):
        # if the use is authorized to coordinate the session, (s)he won't go through the usual mechanisms
        if not self._session.isClosed() and self._session.canCoordinate(self.getAW()):
            return
        SessionModifBase._checkProtection( self )


class SessionModifUnrestrictedTTCoordinationBase(SessionModifBase):

    def _checkProtection(self):
        if not self._session.isClosed() and self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
            return
        SessionModifBase._checkProtection( self )


class SessionSlotBase(SessionBase):

    def _checkParams( self ):

        try:
            SessionBase._checkParams(self)

            l = locators.WebLocator()
            l.setSlot( self._params )
            self._slot = self._target = l.getObject()
            self._session = self._slot.getSession()
            self._conf = self._session.getConference()

#        self._session = self._target
#
#        try:
#            self._slot = self._target = self._session.getSlotById(self._params["slot"])
#            if self._target == None:
#                raise ServiceError("ERR-S3", "Invalid slot id.")
#        except ServiceError, e:
#            raise
#        except Exception, e:
#           raise ServiceError("ERR-S3", "Invalid slot id.",inner=str(e))
        except Exception, e:
            raise ServiceError("ERR-S3", "Invalid slot id.%s"%self._params,inner=str(e))

class SessionSlotDisplayBase(ProtectedDisplayService, SessionSlotBase):

    def _checkParams(self):
        SessionSlotBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)


class SessionSlotModifBase(SessionModifBase, SessionSlotBase):

    def _checkParams( self ):
        SessionSlotBase._checkParams(self)
        if self._params.has_key("scheduleEntry"):
            self._schEntry = self._slot.getSchedule().getEntryById(self._params["scheduleEntry"])
            if self._schEntry == None:
                raise ServiceError("ERR-E4", "Invalid scheduleEntry id.")

    def _checkProtection(self):
        # if the use is authorized to coordinate the session, (s)he won't go through the usual mechanisms
        SessionModifBase._checkProtection(self)

class SessionSlotModifCoordinationBase(SessionSlotModifBase, SessionModifCoordinationBase):

    def _checkProtection(self):
        SessionModifCoordinationBase._checkProtection( self )


class SessionProtectionUserList(SessionModifBase):
    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._session.getAllowedToAccessList())


class SessionProtectionAddUsers(SessionModifBase):
    def _getAccessList(self):
        result = fossilize(self._session.getAllowedToAccessList())
        # get pending users
        for email in self._session.getAccessController().getAccessEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def _checkParams(self):
        SessionModifBase._checkParams(self)
        self._principals = [principal_from_fossil(f, allow_pending=True) for f in self._params['value']]
        self._user = self.getAW().getUser()

    def _getAnswer(self):
        for principal in self._principals:
            self._session.grantAccess(principal)
        return self._getAccessList()


class SessionProtectionRemoveUser(SessionModifBase):

    def _checkParams(self):
        SessionModifBase._checkParams(self)
        self._principal = principal_from_fossil(self._params['value'])
        self._user = self.getAW().getUser()

    def _getAnswer(self):
        self._session.revokeAccess(self._principal)


class SessionChairListBase(SessionModifBase):

    def _checkParams(self):
        SessionModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._kindOfList = pm.extract("kindOfList", pType=str, allowEmpty=False)

    def _getSessionChairList(self):
        # get the lists we need to iterate
        if self._kindOfList == "manager":
            list = self._session.getManagerList()
            pendingList = self._session.getAccessController().getModificationEmail()
        elif self._kindOfList == "coordinator":
            list = self._session.getCoordinatorList()
            pendingList = self._session.getConference().getPendingQueuesMgr().getPendingCoordinatorsKeys()
        result = []
        for sessionChair in list:
            sessionChairFossil = fossilize(sessionChair)
            if isinstance(sessionChair, AvatarUserWrapper):
                isConvener = False
                if self._session.hasConvenerByEmail(sessionChair.getEmail()):
                    isConvener = True
                sessionChairFossil['isConvener'] = isConvener
            result.append(sessionChairFossil)
        # get pending users
        for email in pendingList:
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result


class SessionAddExistingChair(SessionChairListBase):

    def _checkParams(self):
        SessionChairListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._principals = [principal_from_fossil(f, allow_pending=True)
                            for f in pm.extract("userList", pType=list, allowEmpty=False)]

    def _getAnswer(self):
        for principal in self._principals:
            if self._kindOfList == "manager":
                self._session.grantModification(principal)
            elif self._kindOfList == "coordinator":
                self._session.addCoordinator(principal)
        return self._getSessionChairList()


class SessionRemoveChair(SessionChairListBase):

    def _checkParams(self):
        SessionChairListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._chairId = pm.extract("userId", pType=str, allowEmpty=False)
        self._kindOfUser = pm.extract("kindOfUser", pType=str, allowEmpty=True, defaultValue=None)

    def _getAnswer(self):
        if self._kindOfUser == "pending":
            if self._kindOfList == "manager":
                # remove pending email, self._chairId is an email address
                self._session.getAccessController().revokeModificationEmail(self._chairId)
            elif self._kindOfList == "coordinator":
                try:
                    chairSession = self._session.getConference().getPendingQueuesMgr().getPendingCoordinators()[self._chairId][0]
                    self._session.getConference().getPendingQueuesMgr().removePendingCoordinator(chairSession)
                except KeyError:
                    # the user is not in the list of conveners (the table is not updated). Do nothing and update the list
                    pass
        else:
            principal = principal_from_fossil(self._params['principal'])
            if self._kindOfList == "manager":
                self._session.revokeModification(principal)
            elif self._kindOfList == "coordinator":
                self._session.removeCoordinator(principal)
        return self._getSessionChairList()


class SessionModifyAsConvener(SessionChairListBase):

    def _checkParams(self):
        SessionChairListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._chairId = pm.extract("userId", pType=str, allowEmpty=False)


class SessionAddAsConvener(SessionModifyAsConvener):

    def _getAnswer(self):
        ah = AvatarHolder()
        convener = SessionChair()
        convener.setDataFromAvatar(ah.getById(self._chairId))
        self._session.addConvener(convener)
        # get both list for the result
        self._kindOfList = "manager"
        managerResult = self._getSessionChairList()
        self._kindOfList = "coordinator"
        coordinatorResult = self._getSessionChairList()
        return [managerResult, coordinatorResult]


class SessionRemoveAsConvener(SessionModifyAsConvener):

    def _getAnswer(self):
        ah = AvatarHolder()
        convEmail = ah.getById(self._chairId).getEmail()
        for convener in self._session.getConvenerList():
            if convEmail == convener.getEmail():
                self._session.removeConvener(convener)
        # get both list for the result
        self._kindOfList = "manager"
        managerResult = self._getSessionChairList()
        self._kindOfList = "coordinator"
        coordinatorResult = self._getSessionChairList()
        return [managerResult, coordinatorResult]


class SessionProtectionToggleDomains(SessionModifBase):

    def _checkParams(self):
        self._params['sessionId'] = self._params['targetId']
        SessionModifBase._checkParams(self)
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

class SessionGetChildrenProtected(SessionModifBase):

    def _getAnswer(self):
        return fossilize(self._session.getAccessController().getProtectedChildren())

class SessionGetChildrenPublic(SessionModifBase):

    def _getAnswer(self):
        return fossilize(self._session.getAccessController().getPublicChildren())

methodMap = {
    "protection.getAllowedUsersList": SessionProtectionUserList,
    "protection.addAllowedUsers": SessionProtectionAddUsers,
    "protection.removeAllowedUser": SessionProtectionRemoveUser,
    "protection.addExistingManager": SessionAddExistingChair,
    "protection.removeManager": SessionRemoveChair,
    "protection.addAsConvener": SessionAddAsConvener,
    "protection.removeAsConvener": SessionRemoveAsConvener,
    "protection.addExistingCoordinator": SessionAddExistingChair,
    "protection.removeCoordinator": SessionRemoveChair,
    "protection.toggleDomains": SessionProtectionToggleDomains,
    "protection.getProtectedChildren": SessionGetChildrenProtected,
    "protection.getPublicChildren": SessionGetChildrenPublic
}
