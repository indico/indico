from MaKaC.services.implementation.base import ServiceBase
from MaKaC.common import Config


class GetTimezones(ServiceBase):

    def _getAnswer(self):
        cfg = Config.getInstance()
        return cfg.getTimezoneList()
