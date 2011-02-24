#import syslog
import re
from MaKaC.common import DBMgr
import MaKaC.webinterface.rh.base as base
from indico.web.wsgi import indico_wsgi_handler_utils
import MaKaC.common.info as info

class RHChangeLang(base.RH):

    def _process(self):
        params = self._getRequestParams()
        # No need to do any processing here. The language change is processed in RH base
        # Remove lang param from referer
        referer = re.sub(r'(?<=[&?])lang=[^&]*&?', '', params['REFERER_URL'])
        referer = re.sub(r'[?&]$', '', referer)
        self._redirect(referer, noCache=True)
