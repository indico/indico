# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Indico HTTP export API
"""

from indico.web.http_api.export import ExportInterface, LimitExceededException, Exporter

API_MODE_KEY            = 0 # public requests without API key, authenticated requests with api key
API_MODE_ONLYKEY        = 1 # all requests require an API key
API_MODE_SIGNED         = 2 # public requests without API key, authenticated requests with api key and signature
API_MODE_ONLYKEY_SIGNED = 3 # all requests require an API key, authenticated requests need signature
API_MODE_ALL_SIGNED     = 4 # all requests require an api key and a signature

API_MODES = (API_MODE_KEY, API_MODE_ONLYKEY, API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED)