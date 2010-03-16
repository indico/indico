"""
Session-related services
"""

from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.services.implementation.base import ProtectedDisplayService
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.roomBooking import GetBookingBase
import MaKaC.conference as conference
from MaKaC.common.PickleJar import DictPickler
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.services.implementation import conference as conferenceServices
import MaKaC.webinterface.locators as locators
from MaKaC.conference import SessionSlot

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
#            raise e
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

methodMap = {
    "getBooking": SessionGetBooking
}
