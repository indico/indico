from MaKaC.webinterface.rh import users


def index(req, **params):
    return users.RHUserBaskets( req ).process( params )

