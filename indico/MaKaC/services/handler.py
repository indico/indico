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

try:
    from indico.web.wsgi import webinterface_handler_config as apache
except ImportError:
    pass
import MaKaC.services.interface.rpc.json as jsonrpc


def handler(req):
    # runs services according to the URL
    if req.uri.endswith('json-rpc'):
        return jsonrpc_handler(req)
    elif req.uri.endswith('test'):
        return test_handler(req)
    else:
        req.write('Service not found!')
        return apache.HTTP_NOT_FOUND

def jsonrpc_handler(req):
    return jsonrpc.process(req)

def test_handler(req):
    req.write("InDiCo")
    return apache.HTTP_OK
