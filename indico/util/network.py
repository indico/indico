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

"""
Network-related utility functions
"""

from MaKaC.common.info import HelperMaKaCInfo


def _get_remote_ip(req):
    hostIP = str(req.get_remote_ip())

    minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
    if minfo.useProxy():
        # if we're behind a proxy, use X-Forwarded-For
        return req.headers_in.get("X-Forwarded-For", hostIP).split(", ")[-1]
    else:
        return hostIP
