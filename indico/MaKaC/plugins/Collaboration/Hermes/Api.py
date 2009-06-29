from MaKaC.plugins.Collaboration.Hermes.Implementation import RmsApi
from MaKaC.plugins.Collaboration.Hermes.Implementation import McuApi
from MaKaC.plugins.Collaboration.Hermes.Data import HermesBooking
from MaKaC.plugins.Collaboration.Hermes.Tools import parseTime
from MaKaC.common.Configuration import Config
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.rb_room import RoomBase
from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN

def CreateConference(conference, title, start, end, pin, h239):
    id = conference.getNewBookingId()
    namespace = Config.getInstance().getHostNameURL()
    hermesName = namespace + "-" + str(conference.getId()) + "-" + id
    
    try:
        hermesId, pin = RmsApi.CreateConference(hermesName, start, end, pin, h239)
    except Exception, e:
        raise e
    
    booking = HermesBooking(conference)
    booking.setId(id)
    booking.setHermesName(hermesName)
    booking.setHermesId(hermesId)
    booking.setPin(pin)
    booking.setTitle(title)
    booking.setStartingDate(start)
    booking.setEndingDate(end)
    booking.setH239(h239)
    
    conference.addBooking(booking)
    return booking

def DeleteConference(conference, booking):
    booking = conference.getBookingById(booking)
    conference.removeBooking(booking)

def QueryConference(conference, bookingId):
    booking = conference.getBookingById(bookingId)
    if booking == None:
        raise ServiceError("Invalid hermes id.")
    
    #mcuConference = McuApi.first(McuApi.SelectConferences(conferenceName = booking.getHermesName()))
    #if mcuConference == None:
        #raise ServiceError("Conference no longer exists in MCU.", conferenceName)

    roomName = None
    roomAddress = None
    conferenceRoom = conference.getRoom()
    if conferenceRoom:
        roomName = conferenceRoom.getName()
        try:
            DALManagerCERN.connect()
            room = RoomBase.getRooms(roomName = roomName)
            if room:
                roomAddress = room.customAtts["H323 IP"]
        finally:
            DALManagerCERN.disconnect()

    properties = {
        "mcu": McuApi.mcuAddress,
        "roomName": roomName,
        "roomAddress": roomAddress
    }
    return booking, properties

def QueryConferenceStreaming(conference, bookingId):
    booking = conference.getBookingById(bookingId)
    if booking == None:
        raise ServiceError("Invalid hermes id.")
    try:
        response = McuApi.QueryConferenceStreaming(conferenceName = booking.getHermesName())
        streaming = {
            "viewers": response["unicastViewers"] + response["multicastViewers"]
        }
    except:
        streaming = None
    
    return streaming

def ListConferenceParticipant(conference, bookingId):
    booking = conference.getBookingById(bookingId)
    if booking == None:
        raise ServiceError("Invalid hermes id.")
    
    mcuParticipants = McuApi.SelectParticipants({
        "enumerateFilter": "connected",
        "operationScope": ["currentState"]
    }, conferenceName = booking.getHermesName())

    return [{
        "id": participant.get("participantName", ""),
        "name": participant["currentState"].get("displayName", ""),
        "address": participant["currentState"].get("ipAddress", "")
    } for participant in mcuParticipants]

def ConnectConferenceParticipant(conference, bookingId, address):
    booking = conference.getBookingById(bookingId)
    if booking == None:
        raise ServiceError("Invalid hermes id.")
    
    return McuApi.AddParticipant(conferenceName = booking.getHermesName(),
                                 participantType = "ad_hoc",
                                 Address = address)

def DisconnectConferenceParticipant(conference, bookingId, id):
    booking = conference.getBookingById(bookingId)
    if booking == None:
        raise ServiceError("Invalid hermes id.")
    
    return McuApi.RemoveParticipant(conferenceName = booking.getHermesName(),
                                    participantType = "ad_hoc",
                                    participantName = id)
