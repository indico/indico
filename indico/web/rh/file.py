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
from email.Utils import formatdate
from flask import request

from MaKaC.common import Config


def set_file_headers(response, fname, fpath, last_modified, ftype, data, size):
    cfg = Config.getInstance()

    response.content_type = str(cfg.getFileTypeMimeType(ftype))

    dispos = 'attachment' if request.user_agent.platform == 'android' else 'inline'

    response.headers['Content-Length'] = str(size)
    response.headers['Last-Modified'] = formatdate(time.mktime(last_modified.timetuple()))
    response.headers['Content-Disposition'] = '{0}; filename="{1}"'.format(dispos, fname)

    if cfg.getUseXSendFile() and request.user_agent.platform != 'android':
        pass  # TODO - xsf with fpath


def send_file(req, fdata):
    cfg = Config.getInstance()
    if cfg.getUseXSendFile() and req.headers_in['User-Agent'].find('Android') == -1:
        return ""
    else:
        return fdata.readBin()
