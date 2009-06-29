from MaKaC.services.implementation.base import ProtectedModificationService
from MaKaC.plugins.Collaboration.Hermes import Api
from MaKaC.plugins.Collaboration.Hermes.Tools import parseTime
from MaKaC.conference import ConferenceHolder

class HermesService(ProtectedModificationService):
    def _checkParams(self):
        try:
            self._target = ConferenceHolder().getById(self._params["conference"]);
            if self._target == None:
                raise Exception("Null target.")
        except:
            from MaKaC.services.interface.rpc.common import ServiceError
            raise ServiceError("Invalid conference id.")

class CreateConference(HermesService):
    def _getAnswer(self):
        title = self._params["title"]
        start = parseTime(self._params["start"])
        end = parseTime(self._params["end"])
        pin = self._params.get("pin", None)
        h239 = self._params.get("h239", None)
        booking = Api.CreateConference(self._target, title, start, end, pin, h239)
        return {
            "id": booking.getId(),
            "pin": booking.getPin()
        }

class DeleteConference(HermesService):
    def _getAnswer(self):
        id = self._params["id"]
        Api.DeleteConference(self._target, id)

class QueryConference(HermesService):
    def _getAnswer(self):
        id = self._params["id"]
        booking, properties = Api.QueryConference(self._target, id)
        return {
            "title": booking.getTitle(),
            "start": str(booking.getStartingDate()),
            "end": str(booking.getEndingDate()),
            "name": booking.getHermesName(),
            "id": booking.getHermesId(),
            "pin": booking.getPin(),
            "mcu": properties["mcu"],
            "roomName": properties["roomName"],
            "roomAddress": properties["roomAddress"]
        }

class QueryConferenceStreaming(HermesService):
    def _getAnswer(self):
        id = self._params["id"]
        return Api.QueryConferenceStreaming(self._target, id)
    
class ListConferenceParticipant(HermesService):
    def _getAnswer(self):
        id = self._params["id"]
        return Api.ListConferenceParticipant(self._target, id)

class ConnectConferenceParticipant(HermesService):
    def _getAnswer(self):
        id = self._params["id"]
        address = self._params["address"]
        return Api.ConnectConferenceParticipant(self._target, id, address)

class DisconnectConferenceParticipant(HermesService):
    def _getAnswer(self):
        id = self._params["id"]
        participant = self._params["participant"]
        return Api.DisconnectConferenceParticipant(self._target, id, participant)

methodMap = {
    "conference.create": CreateConference,
    "conference.delete": DeleteConference,
    "conference.query": QueryConference,
    "conference.streaming.query": QueryConferenceStreaming,
    "conference.participant.list": ListConferenceParticipant,
    "conference.participant.connect": ConnectConferenceParticipant,
    "conference.participant.disconnect": DisconnectConferenceParticipant
}

