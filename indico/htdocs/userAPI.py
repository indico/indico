from MaKaC.webinterface.rh import api


def index(req, **params):
    return api.RHUserAPI(req).process(params)

def create(req, **params):
    return api.RHUserAPICreate(req).process(params)

def block(req, **params):
    return api.RHUserAPIBlock(req).process(params)

def delete(req, **params):
    return api.RHUserAPIDelete(req).process(params)