# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import os, datetime, time, hashlib

from indico.web.wsgi import webinterface_handler_config as apache

from MaKaC.common import Config
from MaKaC.common.logger import Logger
from MaKaC.errors import MaKaCError

from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.rh import base

from email.Utils import formatdate

import MaKaC.common.TemplateExec as templateEngine

class RHTemplateContentJS(base.RH):
    _uh = urlHandlers.Build("JSContent.py")
    _tplName = ''

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

    def _setHeaders(self):
        # send out the Etag and Last-Modified headers
        creationTime = datetime.datetime.fromtimestamp(os.path.getctime(self._htmlPath))
        self._req.headers_out["Etag"] = self._generateEtag(creationTime)
        self._req.headers_out["Last-Modified"] = formatdate(time.mktime(creationTime.timetuple()))
        self._req.content_type = "application/x-javascript"

    def process( self, params ):

        # Check incoming headers
        self._etag = self._req.headers_in.get("If-None-Match", None)
        # (not used)
        self._modifiedSince = self._req.headers_in.get("If-Modified-Since", None)

        cfg = Config.getInstance()
        dirName = "js"
        fileName = cfg.getTPLFile( self._tplName )

        if fileName == "":
            fileName = "%s.tpl"%self._tplName

        self._tplFile = os.path.join(dirName, fileName)

        self._htmlPath = os.path.join(cfg.getTempDir(), fileName+".tmp")

        # if the file has already been generated
        if os.access(self._htmlPath, os.R_OK):

            # get the OS creation time
            creationTime = datetime.datetime.fromtimestamp(os.path.getctime(self._htmlPath))
            if not self._needsRefresh(creationTime):
                # if the etag the same, send NOT_MODIFIED
                self._req.status = apache.HTTP_NOT_MODIFIED
                return
            else:
                # Read and send the file
                fh = open(self._htmlPath, "r")
                self._htmlData = fh.read()
                fh.close()
                self._setHeaders()
                return self._htmlData
        # file needs to be regenerated
        return base.RH.process(self, params)


    def _process( self ):
        try:
            # regenerate file is needed
            self._dict["__rh__"] = self
            self._dict["user"] = None

            self._htmlData = templateEngine.render(self._tplFile, self._dict)
            fh = open(self._htmlPath, "w")
            fh.write(self._htmlData)
            fh.close()

            self._setHeaders()

        except Exception, e:
            Logger.get('vars_js').exception('Problem generating vars.js')
            return 'indicoError: %s' % e

        return self._htmlData

class RHGetVarsJs(RHTemplateContentJS):
    _uh = urlHandlers.Derive(RHTemplateContentJS, "getVars")

    _tplName = 'vars.js'

    def __init__(self, req):
        RHTemplateContentJS.__init__(self, req)
        self._dict = {}

    @classmethod
    def removeTmpVarsFile(cls):
        cfg = Config.getInstance()
        fileName = cfg.getTPLFile( cls._tplName )

        if fileName == "":
            fileName = "%s.tpl"%cls._tplName

        htmlPath = os.path.join(cfg.getTempDir(), fileName+".tmp")
        if os.access(htmlPath, os.R_OK):
            os.remove(htmlPath)
