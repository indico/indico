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
from indico.web.http_api.responses import HTTPAPIError
from indico.web.wsgi import webinterface_handler_config as apache
import urllib, hmac, hashlib, time
from indico.web.http_api.auth import APIKey
from MaKaC.common.Configuration import Config

"""
Utility functions
"""


def get_query_parameter(queryParams, keys, default=None, integer=False):
    if type(keys) != list:
        keys = [keys]
    for k in keys:
        paramlist = queryParams.get(k)
        if paramlist:
            if len(paramlist) == 1:
                val = paramlist[0]
                if integer:
                    val = int(val)
                del queryParams[k]
                return val
            else:
                raise HTTPAPIError("duplicate argument '%s'" % k, apache.HTTP_BAD_REQUEST)
    return default

def remove_lists(data):
    return dict((k, v[0]) for (k, v) in data.iteritems() if v != None)

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

def generate_public_auth_request(apiMode, apiKey, path, params= {}, persistent=False, https = True):
    from indico.web.http_api import API_MODE_KEY, API_MODE_ONLYKEY, API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED

    key = apiKey.getKey() if apiKey else None
    secret_key = apiKey.getSignKey() if apiKey else None
    if https:
        baseURL = Config.getInstance().getBaseSecureURL()
    else:
        baseURL = Config.getInstance().getBaseURL()
    publicRequestsURL = None
    authRequestURL = None
    if apiMode == API_MODE_KEY:
        publicRequestsURL = build_indico_request(path, params)
        authRequestURL = build_indico_request(path, params, key) if key else None
    elif apiMode == API_MODE_ONLYKEY:
        authRequestURL = build_indico_request(path, params, key) if key else None
        params["onlypublic"] = "yes"
        publicRequestsURL = build_indico_request(path, params, key) if key else None
    elif apiMode == API_MODE_SIGNED:
        publicRequestsURL = build_indico_request(path, params)
        authRequestURL = build_indico_request(path, params, key, secret_key, persistent)  if key and secret_key else None
    elif apiMode == API_MODE_ONLYKEY_SIGNED:
        publicRequestsURL = build_indico_request(path, params, key)  if key else None
        authRequestURL = build_indico_request(path, params, key, secret_key, persistent)  if key and secret_key else None
    elif apiMode == API_MODE_ALL_SIGNED:
        authRequestURL = build_indico_request(path, params, key, secret_key, persistent)  if key else None
        params["onlypublic"] = "yes"
        publicRequestsURL = build_indico_request(path, params, key, secret_key, persistent)  if key else None
    return {"publicRequestURL": (baseURL + publicRequestsURL) if publicRequestsURL else "", "authRequestURL": (baseURL + authRequestURL) if authRequestURL else ""}
