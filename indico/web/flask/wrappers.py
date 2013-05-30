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

from __future__ import absolute_import

from flask import Flask
from flask.wrappers import Request
from werkzeug.utils import cached_property

from MaKaC.common import HelperMaKaCInfo
from indico.web.flask.session import IndicoSessionInterface


class IndicoRequest(Request):
    @cached_property
    def remote_addr(self):
        """The remote address of the client."""
        proxy_ip = None
        if HelperMaKaCInfo.getMaKaCInfoInstance().useProxy() and 'HTTP_X_FORWARDED_FOR' in self.environ:
            proxy_ip = self.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        return proxy_ip or self.environ['REMOTE_ADDR']


class IndicoFlask(Flask):
    request_class = IndicoRequest
    session_interface = IndicoSessionInterface()