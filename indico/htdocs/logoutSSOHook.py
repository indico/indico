import MaKaC.webinterface.rh.login as login
def index(req, **args): 
    return login.RHLogoutSSOHook(req).process(args)

