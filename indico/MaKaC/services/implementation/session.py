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

class SessionBase(conferenceServices.ConferenceBase):

    def _checkParams( self ):

        conferenceServices.ConferenceBase._checkParams(self)

        self._conf = self._target

        try:
            self._session = self._target = self._conf.getSessionById(self._params["session"])
            if self._target == None:
                raise ServiceError("ERR-S4", "Invalid session id.")
        except:
            raise ServiceError("ERR-S4", "Invalid session id.")

class SessionModifBase(SessionBase, ProtectedModificationService):

    def _checkProtection(self):
        # if the use is authorized to coordinate the session, (s)he won't go through the usual mechanisms
        if self._target.canCoordinate(self.getAW()):
            return
        ProtectedModificationService._checkProtection(self)

class SessionSlotBase(SessionBase):

    def _checkParams( self ):

        SessionBase._checkParams(self)

        self._session = self._target

        try:
            self._slot = self._target = self._session.getSlotById(self._params["slot"])
            if self._target == None:
                raise ServiceError("ERR-S3", "Invalid slot id.")
        except ServiceError, e:
            raise e
        except Exception, e:
           raise ServiceError("ERR-S3", "Invalid slot id.",inner=str(e))

class SessionSlotDisplayBase(ProtectedDisplayService, SessionSlotBase):

    def _checkParams(self):
        SessionSlotBase._checkParams(self)
        ProtectedDisplayService._checkParams(self)


class SessionSlotModifBase(SessionSlotBase, ProtectedModificationService):

    def _checkParams( self ):
        SessionSlotBase._checkParams(self)

    def _checkProtection(self):
        # if the use is authorized to coordinate the session, (s)he won't go through the usual mechanisms
        if self._session.canCoordinate(self.getAW()):
            return
        ProtectedModificationService._checkProtection(self)

class SessionSlotScheduleModifBase(SessionSlotModifBase):

    def _checkParams( self ):
        SessionSlotModifBase._checkParams(self)

        self._schEntry = self._slot.getSchedule().getEntryById(self._params["scheduleEntry"])
        if self._schEntry == None:
            raise ServiceError("ERR-E4", "Invalid scheduleEntry id. dd" + self._params["scheduleEntry"] )

class SessionGetBooking(SessionBase, GetBookingBase):
    pass

methodMap = {
    "getBooking": SessionGetBooking
}
