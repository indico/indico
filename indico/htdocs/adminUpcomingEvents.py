from MaKaC.webinterface.rh import admins

def index(req, **params):
    return admins.RHConfigUpcoming(req).process(params)
