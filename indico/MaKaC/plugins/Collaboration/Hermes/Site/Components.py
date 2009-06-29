import os
from os.path import dirname
import sys

from MaKaC.webinterface import wcomponents
import MaKaC.common.Configuration as Configuration

class WComponent(wcomponents.WTemplated):
    def __init__(self, conf):
        self.conf = conf
        self.helpFile = ""
   
    def _setTPLFile(self):
        """Sets the TPL (template) file for the object. It will try to get
            from the configuration if there's a special TPL file for it and
            if not it will look for a file called as the class name+".tpl"
            in the configured TPL directory.
        """
        cfg = Configuration.Config.getInstance()
        dir = dirname(sys.modules[__name__].__file__)
        file = cfg.getTPLFile(self.tplId)
        if file == "":
            file = "%s.tpl" % self.tplId
        self.tplFile = os.path.join(dir, file)
    
class WCreate(WComponent):
    pass

class WShow(WComponent):
    def __init__(self, conf, booking):
        WComponent.__init__(self, conf)
        self.booking = booking
