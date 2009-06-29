import MaKaC.webinterface.rh.resetTimezone as resetTimezone
def index(req, **args):
    args['REFERER_URL'] = (str(req.headers_in['Referer']))
    return resetTimezone.RHResetTZ(req).process(args)

