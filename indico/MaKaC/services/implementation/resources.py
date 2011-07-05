from MaKaC.services.implementation.base import ServiceBase
from MaKaC.common import Config
from indico.util.i18n import getLocaleDisplayNames


class GetTimezones(ServiceBase):

    def _getAnswer(self):
        cfg = Config.getInstance()
        return cfg.getTimezoneList()
