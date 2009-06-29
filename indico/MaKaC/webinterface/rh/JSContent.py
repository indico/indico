import os

from MaKaC.common import Config
from MaKaC.common.TemplateExec import TemplateExec
from MaKaC.errors import MaKaCError

from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.rh import base

class RHTemplateContentJS(base.RH):
    _uh = urlHandlers.Build("JSContent.py")

    def __init__(self, req):
        base.RH.__init__(self, req)

    def _process( self ):

        try:        
            cfg = Config.getInstance()
            dir = os.path.join(cfg.getTPLDir(),"js")
            file = cfg.getTPLFile( self._tplName )

            if file == "":
                file = "%s.tpl"%self._tplName

            self._tplFile = os.path.join(dir, file)        

            htmlPath = os.path.join(cfg.getTempDir(), file+".tmp")

            if os.access(htmlPath, os.R_OK):
                fh = open(htmlPath, "r")
                htmlData = fh.read()
                fh.close()
            else:
                fh = open( self._tplFile, "r")
                text = fh.read()
                fh.close()

                self._dict["__rh__"] = self
                self._dict["user"] = None

                htmlData = TemplateExec().executeTemplate( text, self._dict, self._tplName )
                fh = open(htmlPath, "w")
                fh.write(htmlData)
                fh.close()

        except Exception, e:
            return 'indicoError: %s' % e

        return htmlData

class RHGetVarsJs(RHTemplateContentJS):
    _uh = urlHandlers.Derive(RHTemplateContentJS, "getVars")

    def _process( self ):
        self._tplName = 'vars.js';
        self._dict = {}

        return RHTemplateContentJS._process(self)

