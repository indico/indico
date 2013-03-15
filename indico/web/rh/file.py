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

import time
from MaKaC.common import Config
from email.Utils import formatdate


def set_file_headers(req, fname, fpath, last_modified, ftype, data, size):
    cfg = Config.getInstance()

    mimetype = cfg.getFileTypeMimeType(ftype)
    req.content_type = str(mimetype)

    if 'User-Agent' in req.headers_in and \
            req.headers_in['User-Agent'].find('Android') != -1:
        dispos = "attachment"
    else:
        dispos = "inline"

    req.headers_out.update({
            "Content-Length": str(size),
            "Last-Modified": formatdate(time.mktime(last_modified.timetuple())),
            "Content-Disposition": '{0}; filename="{1}"'.format(dispos, fname)
            })

    if cfg.getUseXSendFile() and req.headers_in['User-Agent'].find('Android') == -1:
        # X-Send-File support makes it easier, just let the web server
        # do all the heavy lifting

        # send_x_file only sets headers
        req.send_x_file(fpath)


def send_file(req, fdata):
    cfg = Config.getInstance()
    if cfg.getUseXSendFile() and req.headers_in['User-Agent'].find('Android') == -1:
        return ""
    else:
        return fdata.readBin()
