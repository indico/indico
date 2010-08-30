#import syslog
from MaKaC.common import DBMgr
import MaKaC.webinterface.rh.base as base
from indico.web.wsgi import indico_wsgi_handler_utils
import MaKaC.common.info as info

class RHChangeLang(base.RH):

    def _process(self):
        params = self._getRequestParams()
        self._websession.setLang(params.get("lang",""))
        self._redirect(params['REFERER_URL'], noCache=True)
