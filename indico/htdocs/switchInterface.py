from MaKaC.webinterface.rh import switchInterface as rhSwitchInterface

def index(req, **params):
    return rhSwitchInterface.RHSwitch(req).process(params)
