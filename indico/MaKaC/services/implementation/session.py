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


class SessionChairListBase(SessionModifBase):

    def _checkParams(self):
        SessionModifBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._kindOfList = pm.extract("kindOfList", pType=str, allowEmpty=False)

    def _isConvener(self, email):
        for convener in self._session.getConvenerList():
            if email == convener.getEmail():
                return True
        return False

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
            if isinstance(sessionChair, Avatar):
                isConvener = False
                if self._isConvener(sessionChair.getEmail()):
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


class SessionGetChairList(SessionChairListBase):

    def _getAnswer(self):
        return self._getSessionChairList()


class SessionAddExistingChair(SessionChairListBase):

    def _checkParams(self):
        SessionChairListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        ph = PrincipalHolder()
        for user in self._userList:
            if self._kindOfList == "manager":
                self._session.grantModification(ph.getById(user["id"]))
            elif self._kindOfList == "coordinator":
                self._session.addCoordinator(ph.getById(user["id"]))
        return self._getSessionChairList()


class SessionRemoveChair(SessionChairListBase):

    def _checkParams(self):
        SessionChairListBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._chairId = pm.extract("userId", pType=str, allowEmpty=False)
        self._kindOfUser = pm.extract("kindOfUser", pType=str, allowEmpty=False)

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
        elif self._kindOfUser == "principal":
            ph = PrincipalHolder()
            if self._kindOfList == "manager":
                self._session.revokeModification(ph.getById(self._chairId))
            elif self._kindOfList == "coordinator":
                self._session.removeCoordinator(ph.getById(self._chairId))
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


class SessionConvenersBase(SessionModifBase):

    def _isEmailAlreadyUsed(self, email):
        for conv in self._session.getConvenerList():
            if email == conv.getEmail():
                return True
        return False

    def _isSessionManager(self, convener):
        # pendings managers
        if convener.getEmail() in self._session.getAccessController().getModificationEmail():
            return True
        # managers list
        for manager in self._session.getManagerList():
            if convener.getEmail() == manager.getEmail():
                return True
        return False

    def _isSessionCoordinator(self, convener):
        # pendings coordinators
        if convener.getEmail() in self._session.getConference().getPendingQueuesMgr().getPendingCoordinatorsKeys():
            return True
        # coordinator list
        for coord in self._session.getCoordinatorList():
            if convener.getEmail() == coord.getEmail():
                return True
        return False

    def _setConvenerData(self, conv):
        conv.setTitle(self._userData.get("title", ""))
        conv.setFirstName(self._userData.get("firstName", ""))
        conv.setFamilyName(self._userData.get("familyName", ""))
        conv.setAffiliation(self._userData.get("affiliation", ""))
        conv.setEmail(self._userData.get("email", ""))
        conv.setAddress(self._userData.get("address", ""))
        conv.setPhone(self._userData.get("phone", ""))
        conv.setFax(self._userData.get("fax", ""))


    def _getConvenerList(self):
        result = []
        for convener in self._session.getConvenerList():
            convFossil = fossilize(convener)
            convFossil["isManager"] = self._isSessionManager(convener)
            convFossil["isCoordinator"] = self._isSessionCoordinator(convener)
            result.append(convFossil)
        return result


class SessionGetConvenerList(SessionConvenersBase):

    def _getAnswer(self):
        return self._getConvenerList()


class SessionAddExistingConvener(SessionConvenersBase):

    def _checkParams(self):
        SessionConvenersBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)
        # Check if there is already a user with the same email
        for user in self._userList:
            if self._isEmailAlreadyUsed(user["email"]):
                raise ServiceAccessError(_("The email address (%s) of a user you are trying to add is already used by another convener or the user is already added to the list. Convener(s) not added.") % user["email"])

    def _getAnswer(self):
        ah = AvatarHolder()
        for user in self._userList:
            convener = SessionChair()
            convener.setDataFromAvatar(ah.getById(user["id"]))
            self._session.addConvener(convener)
        return self._getConvenerList()


class SessionAddNewConvener(SessionConvenersBase):

    def _checkParams(self):
        SessionConvenersBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userData = pm.extract("userData", pType=dict, allowEmpty=False)
        email = self._userData.get("email", "")
        # check if the email is empty and the user wants to give any rights
        if (email == "" and (self._userData.get("manager", False) or self._userData.get("coordinator", False))):
            raise ServiceAccessError(_("It is not possible to grant any rights to a convener with an empty email address. Convener not added."))
        if (email != "" and self._isEmailAlreadyUsed(email)):
            raise ServiceAccessError(_("The email address (%s) is already used by another convener or the user is already added to the list. Convener not added.") % email)

    def _getAnswer(self):
        conv = SessionChair()
        self._setConvenerData(conv)
        self._session.addConvener(conv)
        if (self._userData.get("manager", False)):
            # Add to pending managers list
            self._session.grantModification(conv)
        if (self._userData.get("coordinator", False)):
            # Add to pending managers list
            self._session.addCoordinator(conv)
        return self._getConvenerList()


class SessionConvenerActionBase(SessionConvenersBase):

    def _checkParams(self):
        SessionConvenersBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._convener = self._session.getConvenerById(pm.extract("userId", pType=str, allowEmpty=False))
        if self._convener == None:
            raise ServiceError("ERR-U0", _("User does not exist."))


class SessionGetConvenerData(SessionConvenerActionBase):

    def _getAnswer(self):
        result = fossilize(self._convener)
        result["isManager"] = self._isSessionManager(self._convener)
        result["isCoordinator"] = self._isSessionCoordinator(self._convener)
        return result


class SessionEditConvenerData(SessionConvenerActionBase):

    def _checkParams(self):
        SessionConvenerActionBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._userData = pm.extract("userData", pType=dict, allowEmpty=False)
        email = self._userData.get("email", "")
        if (email == "" and (self._userData.get("manager", False) or self._userData.get("coordinator", False))):
            raise ServiceAccessError(_("It is not possible to grant any rights to a convener with an empty email address. Convener not edited."))
        if (email != "" and self._isEmailUsedByOther()):
            raise ServiceAccessError(_("The email address (%s) is already used by another convener. Convener data not edited.") % email)

    def _isEmailUsedByOther(self):
        for conv in self._session.getConvenerList():
            if self._userData.get("email") == conv.getEmail() and self._convener.getId() != conv.getId():
                return True
        return False

    def _getAnswer(self):
        prevEmail = self._convener.getEmail()
        newEmail = self._userData.get("email", "")
        isSessionCoordinator = self._isSessionCoordinator(self._convener)
        isSessionManager = self._isSessionManager(self._convener)
        self._setConvenerData(self._convener)
        if prevEmail != newEmail:
            if isSessionCoordinator:
                # remove the previous email in queue
                try:
                    del self._session.getConference().getPendingQueuesMgr().getPendingCoordinators()[prevEmail]
                    # add the new email to the list
                    self._session.addCoordinator(self._convener)
                except KeyError:
                    self._session.addCoordinator(self._convener)
            if isSessionManager:
                self._session.getAccessController().revokeModificationEmail(prevEmail)
                self._session.grantModification(self._convener)
        if (self._userData.get("manager", False)):
            # Add to pending managers list
            self._session.grantModification(self._convener)
        if (self._userData.get("coordinator", False)):
            # Add to pending managers list
            self._session.addCoordinator(self._convener)
        return self._getConvenerList()


class SessionRemoveConvener(SessionConvenerActionBase):

    def _getAnswer(self):
        self._session.removeConvener(self._convener)
        return self._getConvenerList()


class SessionModifyConvenerRights(SessionConvenerActionBase):

    def _checkParams(self):
        SessionConvenerActionBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._kindOfRights = pm.extract("kindOfRights", pType=str, allowEmpty=False)


class SessionGrantRights(SessionModifyConvenerRights):

    def _getAnswer(self):
        if self._convener.getEmail() != "":
            if self._kindOfRights == "management":
                self._session.grantModification(self._convener)
            elif self._kindOfRights == "coordination":
                self._session.addCoordinator(self._convener)
        else:
            raise ServiceAccessError(_("It is not possible to grant any rights to a convener with an empty email address. Please, set an email address for this convener."))
        return self._getConvenerList()


class SessionRevokeRights(SessionModifyConvenerRights):

    def _getAnswer(self):
        av = AvatarHolder().match({"email": self._convener.getEmail()})
        if self._kindOfRights == "management":
            if not av:
                self._session.getAccessController().revokeModificationEmail(self._convener.getEmail())
            else:
                self._session.revokeModification(av[0])
        elif self._kindOfRights == "coordination":
            if not av:
                chairSession = self._session.getConference().getPendingQueuesMgr().getPendingCoordinators()[self._convener.getEmail()][0]
                self._session.getConference().getPendingQueuesMgr().removePendingCoordinator(chairSession)
            else:
                self._session.removeCoordinator(av[0])
        return self._getConvenerList()




methodMap = {
    "getBooking": SessionGetBooking,
    "protection.getAllowedUsersList": SessionProtectionUserList,
    "protection.addAllowedUsers": SessionProtectionAddUsers,
    "protection.removeAllowedUser": SessionProtectionRemoveUser,
    "protection.addExistingManager": SessionAddExistingChair,
    "protection.removeManager": SessionRemoveChair,
    "protection.getManagerList": SessionGetChairList,
    "protection.addAsConvener": SessionAddAsConvener,
    "protection.removeAsConvener": SessionRemoveAsConvener,
    "protection.addExistingCoordinator": SessionAddExistingChair,
    "protection.removeCoordinator": SessionRemoveChair,
    "protection.getCoordinatorList": SessionGetChairList,

    "conveners.addExistingConvener": SessionAddExistingConvener,
    "conveners.addNewConvener": SessionAddNewConvener,
    "conveners.getConvenerData": SessionGetConvenerData,
    "conveners.editConvenerData": SessionEditConvenerData,
    "conveners.removeConvener": SessionRemoveConvener,
    "conveners.getConvenerList": SessionGetConvenerList,
    "conveners.grantRights": SessionGrantRights,
    "conveners.revokeRights": SessionRevokeRights
}
