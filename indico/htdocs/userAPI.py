from MaKaC.webinterface.rh import api


def index(req, **params):
    return api.RHUserAPI(req).process(params)

def create(req, **params):
    return api.RHUserAPICreate(req).process(params)