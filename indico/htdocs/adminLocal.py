import MaKaC.webinterface.rh.admins as admins


def index( req, **params ):
    return admins.RHAdminLocalDefinitions( req ).process( params )

def saveTemplateSet( req, **params ):
    return admins.RHAdminSaveTemplateSet( req ).process( params )
