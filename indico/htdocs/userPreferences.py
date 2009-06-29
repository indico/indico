from MaKaC.webinterface.rh import users


def index(req, **params):
    return users.RHUserPreferences( req ).process( params )

