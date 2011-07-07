"""
Session-related services
"""

from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.roomBooking import GetBookingBase
import MaKaC.conference as conference
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError
from MaKaC.services.implementation import conference as conferenceServices
import MaKaC.webinterface.locators as locators
from MaKaC.conference import SessionSlot, SessionChair
from MaKaC.common.fossilize import fossilize
from MaKaC.user import PrincipalHolder, Avatar, Group, AvatarHolder

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
        if self._session.canCoordinate(self.getAW()):
            return
        SessionModifBase._checkProtection( self )


class SessionModifUnrestrictedTTCoordinationBase(SessionModifBase):

    def _checkProtection(self):
        if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
            return
        SessionModifBase._checkProtection( self )


class SessionModifUnrestrictedContribMngCoordBase(SessionModifBase):

    def _checkProtection(self):
        if self._session.canCoordinate(self.getAW(), "modifContribs"):
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


class SessionSlotModifBase(SessionSlotBase, SessionModifBase):

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

class SessionSlotModifUnrestrictedTTCoordinationBase(SessionSlotModifBase, SessionModifUnrestrictedTTCoordinationBase):

    def _checkProtection(self):
        SessionModifUnrestrictedTTCoordinationBase._checkProtection( self )

class SessionSlotModifUnrestrictedContribMngCoordBase(SessionSlotModifBase, SessionModifUnrestrictedContribMngCoordBase):

    def _checkProtection(self):
        SessionModifUnrestrictedContribMngCoordBase._checkProtection( self )

class SessionGetBooking(SessionBase, GetBookingBase):
    pass

class SessionProtectionUserList(SessionModifBase):
    def _getAnswer(self):
        #will use IAvatarFossil or IGroupFossil
        return fossilize(self._session.getAllowedToAccessList())

class SessionProtectionAddUsers(SessionModifBase):

    def _checkParams(self):
        SessionModifBase._checkParams(self)

        self._usersData = self._params['value']
        self._user = self.getAW().getUser()

    def _getAnswer(self):

        for user in self._usersData :

            userToAdd = PrincipalHolder().getById(user['id'])

            if not userToAdd :
                raise ServiceError("ERR-U0","User does not exist!")

            self._session.grantAccess(userToAdd)

class SessionProtectionRemoveUser(SessionModifBase):

    def _checkParams(self):
        SessionModifBase._checkParams(self)

        self._userData = self._params['value']

        self._user = self.getAW().getUser()

    def _getAnswer(self):

        userToRemove = PrincipalHolder().getById(self._userData['id'])

        if not userToRemove :
            raise ServiceError("ERR-U0","User does not exist!")
        elif isinstance(userToRemove, Avatar) or isinstance(userToRemove, Group) :
            self._session.revokeAccess(userToRemove)


class SessionManagerListBase(SessionModifBase):

    def _isConvener(self, email):
        for convener in self._session.getConvenerList():
            if email == convener.getEmail():
                return True
        return False

    def _getManagersList(self):
        result = []
        for manager in self._session.getManagerList():
            managerFossil = fossilize(manager)
            if isinstance(manager, Avatar):
                isConvener = False
                if self._isConvener(manager.getEmail()):
                    isConvener = True
                managerFossil['isConvener'] = isConvener
            result.append(managerFossil)
        # get pending users
        for email in self._session.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result


class SessionGetManagerList(SessionManagerListBase):

    def _getAnswer(self):
        return self._getManagersList()


class SessionAddExistingManager(SessionManagerListBase):

    def _checkParams(self):
        SessionManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        for user in self._userList:
            self._session.grantModification(ph.getById(user["id"]))
        return self._getManagersList()


class SessionRemoveManager(SessionManagerListBase):

    def _checkParams(self):
        SessionManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._managerId = pm.extract("userId", pType=str, allowEmpty=False)
        self._kindOfUser = pm.extract("kindOfUser", pType=str, allowEmpty=False)

    def _getAnswer(self):
        if self._kindOfUser == "pending":
            # remove pending email, self._submitterId is an email address
            self._session.getAccessController().revokeModificationEmail(self._managerId)
        elif self._kindOfUser == "principal":
            ph = PrincipalHolder()
            self._session.revokeModification(ph.getById(self._managerId))
        return self._getManagersList()


class SessionModifyAsConvener(SessionManagerListBase):

    def _checkParams(self):
        SessionManagerListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._managerId = pm.extract("userId", pType=str, allowEmpty=False)


class SessionAddAsConvener(SessionModifyAsConvener):

    def _getAnswer(self):
        ah = AvatarHolder()
        convener = SessionChair()
        convener.setDataFromAvatar(ah.getById(self._managerId))
        self._session.addConvener(convener)
        return self._getManagersList()


class SessionRemoveAsConvener(SessionModifyAsConvener):

    def _getAnswer(self):
        ah = AvatarHolder()
        convEmail = ah.getById(self._managerId).getEmail()
        for convener in self._session.getConvenerList():
            if convEmail == convener.getEmail():
                self._session.removeConvener(convener)
        return self._getManagersList()



methodMap = {
    "getBooking": SessionGetBooking,
    "protection.getAllowedUsersList": SessionProtectionUserList,
    "protection.addAllowedUsers": SessionProtectionAddUsers,
    "protection.removeAllowedUser": SessionProtectionRemoveUser,
    "protection.addExistingManager": SessionAddExistingManager,
    "protection.removeManager": SessionRemoveManager,
    "protection.getManagerList": SessionGetManagerList,
    "protection.addAsConvener": SessionAddAsConvener,
    "protection.removeAsConvener": SessionRemoveAsConvener
}
