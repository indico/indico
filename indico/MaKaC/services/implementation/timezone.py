import datetime
from MaKaC.common import Config
import time

from MaKaC.services.implementation.base import ServiceBase
from MaKaC.services.interface.rpc.common import ServiceError

class GetTimezones(ServiceBase):

    def _checkParams(self):
        ServiceBase._checkParams(self)
    
    def _getAnswer(self):
        return {"timezones": Config.getInstance().getTimezoneList()}

methodMap = {
    "getTimezones": GetTimezones
}