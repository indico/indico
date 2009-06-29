from MaKaC.webinterface.rh.conferenceDisplay import RHShortURLRedirect

def index(req, **params):
    return RHShortURLRedirect(req).process(params)