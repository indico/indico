from MaKaC.webinterface.rh import JSContent

def getVars(req, **params):
    return JSContent.RHGetVarsJs( req ).process( params )