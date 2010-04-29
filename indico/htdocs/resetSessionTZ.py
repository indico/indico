import MaKaC.webinterface.rh.resetTimezone as resetTimezone
from MaKaC.common import Config
def index(req, **args):
    args['REFERER_URL'] = (str(req.headers_in.get('Referer', Config.getInstance().getBaseURL())))
    return resetTimezone.RHResetTZ(req).process(args)

