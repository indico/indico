# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import hashlib
import hmac
import time
import urllib

from indico.core.config import config
from indico.modules.api import APIMode, api_settings


def get_query_parameter(queryParams, keys, default=None, integer=False):
    if not isinstance(keys, (list, tuple, set)):
        keys = (keys,)
    for k in keys:
        if k not in queryParams:
            continue
        val = queryParams.pop(k)
        if integer:
            val = int(val)
        return val
    return default


def build_indico_request(path, params, api_key=None, secret_key=None, persistent=False):
    items = params.items() if hasattr(params, 'items') else list(params)
    if api_key:
        items.append(('apikey', api_key))
    if secret_key:
        if not persistent:
            items.append(('timestamp', str(int(time.time()))))
        items = sorted(items, key=lambda x: x[0].lower())
        url = '%s?%s' % (path, urllib.urlencode(items))
        signature = hmac.new(secret_key, url, hashlib.sha1).hexdigest()
        items.append(('signature', signature))
    if not items:
        return path
    return '%s?%s' % (path, urllib.urlencode(items))


def generate_public_auth_request(apiKey, path, params=None):
    apiMode = api_settings.get('security_mode')
    if params is None:
        params = {}
    if apiKey:
        key = apiKey.token
        secret_key = apiKey.secret
        persistent = apiKey.is_persistent_allowed and api_settings.get('allow_persistent')
    else:
        key = secret_key = None
        persistent = False
    publicRequestsURL = None
    authRequestURL = None
    if apiMode == APIMode.KEY:
        publicRequestsURL = build_indico_request(path, params)
        authRequestURL = build_indico_request(path, params, key) if key else None
    elif apiMode == APIMode.ONLYKEY:
        authRequestURL = build_indico_request(path, params, key) if key else None
        params["onlypublic"] = "yes"
        publicRequestsURL = build_indico_request(path, params, key) if key else None
    elif apiMode == APIMode.SIGNED:
        publicRequestsURL = build_indico_request(path, params)
        authRequestURL = build_indico_request(path, params, key, secret_key, persistent)  if key and secret_key else None
    elif apiMode == APIMode.ONLYKEY_SIGNED:
        publicRequestsURL = build_indico_request(path, params, key)  if key else None
        authRequestURL = build_indico_request(path, params, key, secret_key, persistent)  if key and secret_key else None
    elif apiMode == APIMode.ALL_SIGNED:
        authRequestURL = build_indico_request(path, params, key, secret_key, persistent)  if key else None
        params["onlypublic"] = "yes"
        publicRequestsURL = build_indico_request(path, params, key, secret_key, persistent)  if key else None
    return {'publicRequestURL': (config.BASE_URL + publicRequestsURL) if publicRequestsURL else '',
            'authRequestURL': (config.BASE_URL + authRequestURL) if authRequestURL else ''}
