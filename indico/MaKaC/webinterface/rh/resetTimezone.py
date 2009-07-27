#import syslog
from MaKaC.common import DBMgr
import MaKaC.webinterface.rh.base as base
from mod_python import util
import MaKaC.common.info as info
from MaKaC.i18n import _

class RHResetTZ(base.RH):
    
    def _process(self):
        sess = self._aw.getSession()
        #syslog.syslog("In RHResetTZ id: " + str(sess.id))
        parms = self._getRequestParams()
            
        tz = None
        if parms["activeTimezone"] == "My":
            if self._aw.getUser():
                tz = self._aw.getUser().getTimezone()
            else:
                tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        else:
            tz = parms["activeTimezone"]
        
        try:
            if parms["saveToProfile"] == "on":
                user = sess.getUser()
                if tz == "LOCAL":
                    user.setDisplayTZMode(_("Event Timezone"))
                else:
                    user.setTimezone(tz)
                    user.setDisplayTZMode(_("MyTimezone"))
        except:
            pass
        
        sess.setVar("ActiveTimezone", tz)
        # redirect to the calling URL with the new session tz.
        #DBMgr.getInstance().endRequest(True)
        #util.redirect(self._req,parms['REFERER_URL'])
        self._redirect(parms['REFERER_URL'])
