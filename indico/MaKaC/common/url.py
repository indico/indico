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

"""This file contains classes which allow to handle URLs in a transparent way
"""
from flask import url_for
from flask import current_app as app
from werkzeug.urls import url_encode, url_parse, url_unparse, url_join

from MaKaC.common.Configuration import Config
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import MaKaCError


class _BaseURL(object):
    def __init__(self, params):
        self.fragment = None
        self._url = None
        self._modified = True
        self._params = dict(params) if params else {}

    def _rebuild(self):
        raise NotImplementedError

    def setSegment(self, segment):
        self.fragment = segment

    def setParams(self, params):
        self._params = {}
        if params:
            self._params.update(params)
        self._modified = True

    def addParams(self, params):
        self._params.update(params)
        self._modified = True

    def addParam(self, name, value):
        self._params[name] = value
        self._modified = True

    @property
    def url(self):
        # We lazily generate the URL only when it's needed. This has the advantage that we never try to build
        # an URL while not all params are present - while it would not be a big problem when using query string
        # arguments, it would trigger an exception in case a rule argument is missing.
        if self._modified:
            self._modified = False
            self._rebuild()
        return self._url

    @property
    def js_router(self):
        raise NotImplementedError

    def __str__(self):
        return self.url


class URL(_BaseURL):
    def __init__(self, absolute_url, **params):
        _BaseURL.__init__(self, params)
        self._absolute_url = str(absolute_url).strip()
        self._rebuild()

    def _rebuild(self):
        base = url_parse(self._absolute_url)
        params = base.decode_query()
        for key, value in self._params.iteritems():
            params[key] = value
        self._url = url_unparse(base._replace(query=url_encode(params), fragment=self.fragment))

    @property
    def js_router(self):
        return str(self)

    def __repr__(self):
        return '<URL(%s, %r, %s)>' % (self._absolute_url, self._params, self.url)


class EndpointURL(_BaseURL):
    def __init__(self, endpoint, secure, params):
        _BaseURL.__init__(self, params)
        cfg = Config.getInstance()
        self._base_url = cfg.getBaseSecureURL() if secure else cfg.getBaseURL()
        self._endpoint = endpoint
        self._secure = secure

    def _rebuild(self):
        # url_for already creates an absolute url (e.g. /indico/whatever) but since it starts
        # with a slash this is not a problem. It overwrites the path part in baseURL but it's
        # the same one. maybe we could even get rid of the baseURL stuff at some point... It's
        # only really important when we change from SSL to non-SSL or vice versa anyway
        self._url = url_join(self._base_url, url_for(self._endpoint, **self._params))

    @property
    def js_router(self):
        # based on werkzeug.contrib.jsrouting
        return {
            'type': 'flask_rules',
            'rules': [
                {
                    'args': list(rule.arguments),
                    'defaults': rule.defaults,
                    'trace': [
                        {
                            'is_dynamic': is_dynamic,
                            'data': data
                        } for is_dynamic, data in rule._trace
                    ]
                } for rule in app.url_map.iter_rules(self._endpoint)
            ]
        }

    def __repr__(self):
        schema = url_parse(self.url).schema
        return '<EndpointURL(%s, %s, %s, %s)>' % (schema, self._endpoint, self._params, self.url)


class ShortURLMapper(ObjectHolder):

    idxName = "shorturl"

    def add( self, tag, newItem ):
        if not tag:
            raise MaKaCError("Invalid tag for short URL : \"%s\""%tag)
        if self.hasKey(tag):
            raise MaKaCError("Short URL tag already used: \"%s\""%tag)
        tree = self._getIdx()
        tree[tag] = newItem
        return tag

    def remove( self, item ):
        """removes the specified object from the index.
        """
        tree = self._getIdx()
        if not tree.has_key( item.getUrlTag() ):
            return
        del tree[item.getUrlTag()]


