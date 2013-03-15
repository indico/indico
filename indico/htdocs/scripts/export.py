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

"""
This script has been removed. If you wish to obtain metadata from Indico, consider using the new HTTP API:

{indico_server}/ihelp/html/ExportAPI/index.html
"""


from MaKaC.common import Config

def index(req, **params):
    req.content_type = 'text/plain'
    config = Config.getInstance()
    return globals()['__doc__'].format(indico_server=config.getBaseURL())
