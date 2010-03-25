import MaKaC.webinterface.rh.lang as lang
from MaKaC.common import Config
def index(req, **args):
    args['REFERER_URL'] = (str(req.headers_in.get('Referer', Config.getInstance().getBaseURL())))
    return lang.RHChangeLang(req).process(args)

