# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

import os
from email.Utils import formatdate

from indico.core.config import Config
from MaKaC.common.logger import Logger
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.rh import base
import MaKaC.common.TemplateExec as templateEngine

from indico.web.flask.util import send_file


class RHGetVarsJs(base.RH):
    _tplName = 'vars.js'

    def __init__(self, req):
        base.RH.__init__(self, req)
        self._dict = {}

    def process(self, params):
        # Check incoming headers
        cfg = Config.getInstance()
        dirName = "js"
        fileName = cfg.getTPLFile(self._tplName)

        if not fileName:
            fileName = "%s.tpl" % self._tplName

        self._tplFile = os.path.join(dirName, fileName)
        self._cacheFile = os.path.join(cfg.getTempDir(), fileName + ".tmp")

        if not os.access(self._cacheFile, os.R_OK):
            base.RH.process(self, params)
        if not os.access(self._cacheFile, os.R_OK):
            raise MaKaCError('Could not generate JSVars')

        return send_file('vars.js', self._cacheFile, mimetype='application/x-javascript', no_cache=False,
                         conditional=True)

    def _process(self):
        try:
            # regenerate file is needed
            self._dict["__rh__"] = self
            self._dict["user"] = None

            data = templateEngine.render(self._tplFile, self._dict).strip()
            with open(self._cacheFile, "w") as fp:
                fp.write(data)

        except Exception:
            Logger.get('vars_js').exception('Problem generating vars.js')
            raise

    @classmethod
    def removeTmpVarsFile(cls):
        cfg = Config.getInstance()
        fileName = cfg.getTPLFile(cls._tplName)

        if not fileName:
            fileName = "%s.tpl" % cls._tplName

        htmlPath = os.path.join(cfg.getTempDir(), fileName + ".tmp")
        if os.access(htmlPath, os.R_OK):
            os.remove(htmlPath)
