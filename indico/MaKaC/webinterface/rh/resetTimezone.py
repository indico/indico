#import syslog
import MaKaC.webinterface.rh.base as base
import MaKaC.common.info as info

class RHResetTZ(base.RH):

    def _process(self):
        sess = self._aw.getSession()
        #syslog.syslog("In RHResetTZ id: " + str(sess.id))
        parms = self._getRequestParams()

        tz = None
        if not parms.has_key("activeTimezone") or parms["activeTimezone"] == "My":
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
                    user.setDisplayTZMode("Event Timezone")
                else:
                    user.setTimezone(tz)
                    user.setDisplayTZMode("MyTimezone")
        except:
            pass

        sess.setVar("ActiveTimezone", tz)
        # redirect to the calling URL with the new session tz.
        #DBMgr.getInstance().endRequest(True)
        #util.redirect(self._req,parms['REFERER_URL'])
        self._redirect(parms['REFERER_URL'])
