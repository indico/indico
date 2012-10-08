 # -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

import time
from MaKaC.common import Config
from email.Utils import formatdate

class RHFileCommon():

    def _process(self):
        self._req.headers_out["Content-Length"] = "%s" % self._file.getSize()
        self._req.headers_out["Last-Modified"] = "%s" % formatdate(time.mktime(self._file.getCreationDate().timetuple()))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType(self._file.getFileType())
        self._req.content_type = """%s""" % (mimetype)
        dispos = "inline"
        try:
            if self._req.headers_in['User-Agent'].find('Android') != -1:
                dispos = "attachment"
        except KeyError:
            pass
        self._req.headers_out["Content-Disposition"] = '%s; filename="%s"' % (dispos, self._file.getFileName())
        if cfg.getUseXSendFile() and self._req.headers_in['User-Agent'].find('Android') == -1:
            # X-Send-File support makes it easier, just let the web server
            # do all the heavy lifting
            return self._req.send_x_file(self._file.getFilePath())
        else:
            return self._file.readBin()
