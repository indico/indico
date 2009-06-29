import MaKaC.webinterface.rh.lang as lang
def index(req, **args):
    args['REFERER_URL'] = (str(req.headers_in['Referer']))
    return lang.RHChangeLang(req).process(args)

