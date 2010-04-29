from MaKaC.services.implementation import resources
from MaKaC.services.implementation import roomBooking
from MaKaC.services.implementation import error

from MaKaC.services.interface.rpc import description


def importModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


methodMap = {

    "roomBooking.locations.list": roomBooking.RoomBookingListLocations,
    "roomBooking.rooms.list": roomBooking.RoomBookingListRooms,
    "roomBooking.rooms.fullNameList": roomBooking.RoomBookingFullNameListRooms,
    "roomBooking.locationsAndRooms.list" :roomBooking.RoomBookingListLocationsAndRooms,

    "resources.timezones.getAll": resources.GetTimezones,
    "resources.languages.getAll": resources.GetLanguages,

    "system.describe": description.describe,
    "system.error.report": error.SendErrorReport
}


endpointMap = {

    "event": importModule("MaKaC.services.implementation.conference"),
    "user": importModule('MaKaC.services.implementation.user'),
    "contribution": importModule('MaKaC.services.implementation.contribution'),
    "session": importModule('MaKaC.services.implementation.session'),
    "schedule": importModule('MaKaC.services.implementation.schedule'),
    "search": importModule('MaKaC.services.implementation.search'),
    "material": importModule('MaKaC.services.implementation.material'),
    "reviewing": importModule('MaKaC.services.implementation.reviewing'),
    "minutes": importModule('MaKaC.services.implementation.minutes'),
    "news": importModule('MaKaC.services.implementation.news'),
    "collaboration": importModule('MaKaC.services.implementation.collaboration'),
    "plugins": importModule('MaKaC.services.implementation.plugins'),
    "category": importModule('MaKaC.services.implementation.category'),
    "upcomingEvents": importModule('MaKaC.services.implementation.upcoming'),
    "timezone": importModule('MaKaC.services.implementation.timezone'),

    # Hermes integration
    #"hermes": importPlugin('Collaboration', 'Hermes', 'ServiceEndpoint'),

    # Tests - just for remote testing of JSON-RPC
    "test": importModule('MaKaC.services.implementation.test')
}
