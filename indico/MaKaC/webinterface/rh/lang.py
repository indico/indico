#import syslog
from MaKaC.common import DBMgr
import MaKaC.webinterface.rh.base as base
from mod_python import util
import MaKaC.common.info as info

class RHChangeLang(base.RH):
    
    def _process(self):
        params = self._getRequestParams()
        self._websession.setLang(params.get("lang",""))
        self._redirect(params['REFERER_URL'], noCache=True)
