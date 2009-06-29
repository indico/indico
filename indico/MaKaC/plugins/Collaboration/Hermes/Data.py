from MaKaC.booking import Booking

class HermesBooking(Booking):
    def __init__(self, conference):
        Booking.__init__(self, conference)
        self._system = "HERMES"
        self._hermesId = None
        self._hermesName = None
        self._pin = None
        self._h239 = False

    def getHermesId(self):
        return self._hermesId
        
    def setHermesId(self, hermesId):
        self._hermesId = hermesId
        
    def getHermesName(self):
        return self._hermesName
        
    def setHermesName(self, hermesName):
        self._hermesName = hermesName
        
    def getPin(self):
        return self._pin
    
    def setPin(self, pin):
        self._pin = pin

    def getH239(self):
        return self._h239
    
    def setH239(self, h239):
        self._h239 = h239
    
    def deleteBooking(self):
        from MaKaC.plugins.Collaboration.Hermes.Implementation import RmsApi
        try:
            RmsApi.DeleteConference(self.getHermesId())
            message = "Success"
        except Exception, e:
            message = str(e)
        return [message, ""]
    
    def getPublicDescription(self):
        # TODO
        raise Exception("Public description not implemented.")
