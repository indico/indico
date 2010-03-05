import os, datetime, time, hashlib

from mod_python import apache

from MaKaC.common import Config
from MaKaC.common.TemplateExec import TemplateExec
from MaKaC.errors import MaKaCError

from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.rh import base

from email.Utils import formatdate

class RHTemplateContentJS(base.RH):
    _uh = urlHandlers.Build("JSContent.py")

    def __init__(self, req):
        base.RH.__init__(self, req)

    def _needsRefresh( self, creationTime ):
        # TODO: maybe add date verification as well?
        return self._etag != self._generateEtag(creationTime)

    def _generateEtag( self, value ):
        """
        Generates an Etag from a string (just an MD5 hash)
        """
        return hashlib.md5(str(value)).hexdigest()

    def _checkParams( self, params ):

        # Check incoming headers
        self._etag = self._req.headers_in.get("If-None-Match", None)
        # (not used)
        self._modifiedSince = self._req.headers_in.get("If-Modified-Since", None)

        cfg = Config.getInstance()
        dirName = os.path.join(cfg.getTPLDir(),"js")
        fileName = cfg.getTPLFile( self._tplName )

        if fileName == "":
            fileName = "%s.tpl"%self._tplName

        self._tplFile = os.path.join(dirName, fileName)

        self._htmlPath = os.path.join(cfg.getTempDir(), fileName+".tmp")

        # if the file has already been generated
        if os.access(self._htmlPath, os.R_OK):

            self._regenerate = False;

            # get the OS creation time
            creationTime = datetime.datetime.fromtimestamp(os.path.getctime(self._htmlPath))
            if not self._needsRefresh(creationTime):
                # if the etag the same, send NOT_MODIFIED
                self._req.status = apache.HTTP_NOT_MODIFIED
                self._doProcess = False
        else:
            # file needs to be regenerated
            self._regenerate = True;


    def _process( self ):

        try:
            # regenerate file if needed
            if self._regenerate:
                fh = open( self._tplFile, "r")
                text = fh.read()
                fh.close()

                self._dict["__rh__"] = self
                self._dict["user"] = None

                htmlData = TemplateExec().executeTemplate( text, self._dict, self._tplName )
                fh = open(self._htmlPath, "w")
                fh.write(htmlData)
                fh.close()
            else:
                # otherwise just send it to the client
                fh = open(self._htmlPath, "r")
                htmlData = fh.read()
                fh.close()

            # send out the Etag and Last-Modified headers
            creationTime = datetime.datetime.fromtimestamp(os.path.getctime(self._htmlPath))
            self._req.headers_out["Etag"] = self._generateEtag(creationTime)
            self._req.headers_out["Last-Modified"] = formatdate(time.mktime(creationTime.timetuple()))
            self._req.content_type = "application/x-javascript"

        except Exception, e:
            return 'indicoError: %s' % e

        return htmlData

class RHGetVarsJs(RHTemplateContentJS):
    _uh = urlHandlers.Derive(RHTemplateContentJS, "getVars")

    def __init__(self, req):
        RHTemplateContentJS.__init__(self, req)
        self._tplName = 'vars.js';
        self._dict = {}

