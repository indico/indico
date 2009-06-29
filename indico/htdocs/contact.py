from MaKaC.webinterface.rh import contact as rhContact

def index(req, **params):
    return rhContact.RHContact(req).process(params)