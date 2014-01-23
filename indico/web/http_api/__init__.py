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

"""
Indico HTTP export API
"""

from indico.web.http_api.hooks.base import DataFetcher, HTTPAPIHook
from indico.web.http_api.exceptions import LimitExceededException
from indico.web.http_api.hooks.file import FileHook
from indico.web.http_api.hooks.registration import RegistrantsHook
from indico.web.http_api.hooks.user import UserInfoHook


API_MODE_KEY            = 0  # public requests without API key, authenticated requests with api key
API_MODE_ONLYKEY        = 1  # all requests require an API key
API_MODE_SIGNED         = 2  # public requests without API key, authenticated requests with api key and signature
API_MODE_ONLYKEY_SIGNED = 3  # all requests require an API key, authenticated requests need signature
API_MODE_ALL_SIGNED     = 4  # all requests require an api key and a signature

API_MODES = (API_MODE_KEY, API_MODE_ONLYKEY, API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED)
