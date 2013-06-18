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

import os
import re
import time

from flask import request, redirect, url_for, Blueprint
from flask import current_app as app
from flask import send_file as _send_file
from werkzeug.datastructures import Headers, FileStorage
from werkzeug.exceptions import NotFound, HTTPException
from werkzeug.routing import BaseConverter, RequestRedirect
from werkzeug.urls import url_parse

from MaKaC.common import Config
from indico.util.caching import memoize
from indico.web.rh import RHHtdocs


def _convert_request_value(x):
    if isinstance(x, unicode):
        return x.encode('utf-8')
    elif isinstance(x, FileStorage):
        x.file = x.stream
        return x
    raise ValueError('Unexpected item in request data: %s' % type(x))


def create_flat_args():
    args = request.args.copy()
    args.update(request.form)
    args.update(request.files)
    flat_args = {}
    for key, item in args.iterlists():
        flat_args[key] = map(_convert_request_value, item) if len(item) > 1 else _convert_request_value(item[0])
    return flat_args


@memoize
def rh_as_view(rh):
    if issubclass(rh, RHHtdocs):
        def wrapper(filepath, plugin=None):
            path = rh.calculatePath(filepath, plugin=plugin)
            if not os.path.isfile(path):
                raise NotFound
            return _send_file(path)
    else:
        def wrapper(**kwargs):
            params = create_flat_args()
            params.update(kwargs)
            return rh(None).process(params)

    wrapper.__name__ = rh.__name__
    wrapper.__doc__ = rh.__doc__
    return wrapper


def iter_blueprint_rules(blueprint):
    for func in blueprint.deferred_functions:
        yield dict(zip(func.func_code.co_freevars, (c.cell_contents for c in func.func_closure)))


def legacy_rule_from_endpoint(endpoint):
    endpoint = re.sub(r':\d+$', '', endpoint)
    if '-' in endpoint:
        return '/' + endpoint.replace('-', '.py/')
    else:
        return '/' + endpoint + '.py'


def make_compat_redirect_func(blueprint, rule):
    def _redirect():
        # Ugly hack to get non-list arguments unless they are used multiple times.
        # This is necessary since passing a list for an URL path argument breaks things.
        args = dict((k, v[0] if len(v) == 1 else v) for k, v in request.args.iterlists())
        target = url_for('%s.%s' % (blueprint.name, rule['endpoint']), **args)
        return redirect(target)
    return _redirect


def make_compat_blueprint(blueprint):
    compat = Blueprint('compat_' + blueprint.name, __name__)
    used_endpoints = set()
    for rule in iter_blueprint_rules(blueprint):
        if not rule.get('endpoint'):
            continue

        endpoint = rule['endpoint']
        i = 0
        while endpoint in used_endpoints:
            i += 1
            endpoint = '%s:%s' % (rule['endpoint'], i)
        used_endpoints.add(endpoint)

        compat.add_url_rule(legacy_rule_from_endpoint(endpoint), endpoint, make_compat_redirect_func(blueprint, rule),
                            methods=rule['options'].get('methods'))
    return compat


def endpoint_for_url(url):
    urldata = url_parse(url)
    adapter = app.url_map.bind(urldata.netloc)
    try:
        return adapter.match(urldata.path)
    except RequestRedirect, e:
        return endpoint_for_url(e.new_url)
    except HTTPException:
        return None


def send_file(name, path_or_fd, mimetype, last_modified=None, no_cache=True, inline=True, conditional=False):
    # Note: path can also be a StringIO!
    if request.user_agent.platform == 'android':
        # Android is just full of fail when it comes to inline content-disposition...
        inline = False
    if mimetype.isupper() and '/' not in mimetype:
        # Indico file type such as "JPG" or "CSV"
        mimetype = Config.getInstance().getFileTypeMimeType(mimetype)
    rv = _send_file(path_or_fd, mimetype=mimetype, as_attachment=not inline, attachment_filename=name,
                    conditional=conditional)
    if inline:
        # send_file does not add this header if as_attachment is False
        rv.headers.add('Content-Disposition', 'inline', filename=name)
    if last_modified:
        if not isinstance(last_modified, int):
            last_modified = int(time.mktime(last_modified.timetuple()))
        rv.last_modified = last_modified
    if no_cache:
        del rv.expires
        del rv.cache_control.max_age
        rv.cache_control.public = False
        rv.cache_control.private = True
        rv.cache_control.no_cache = True
    return rv


class ListConverter(BaseConverter):
    """Matches a dash-separated list"""

    def __init__(self, map):
        BaseConverter.__init__(self, map)
        self.regex = '\w+(?:-\w+)*'

    def to_python(self, value):
        return value.split('-')

    def to_url(self, value):
        if isinstance(value, (list, tuple, set)):
            value = '-'.join(value)
        return super(ListConverter, self).to_url(value)


class ResponseUtil(object):
    """This class allows "modifying" a Response object before it is actually created.

    The purpose of this is to allow e.g. an Indico RH to trigger a redirect but revoke
    it later in case of an error or to simply have something to pass around to functions
    which want to modify headers while there is no response available.

    When you want a RH to call another RH assign a lambda performing the call to `.call`.
    This ensures it's called after the current RH has finished and cleaned everything up.
    """

    def __init__(self):
        self.headers = Headers()
        self._redirect = None
        self.status = 200
        self.content_type = None
        self.call = None

    @property
    def modified(self):
        return bool(self.headers) or self._redirect or self.status != 200 or self.content_type

    @property
    def redirect(self):
        return self._redirect

    @redirect.setter
    def redirect(self, value):
        if value is None:
            pass
        elif isinstance(value, tuple) and len(value) == 2:
            pass
        else:
            raise ValueError('redirect must be None or a 2-tuple containing URL and status code')
        self._redirect = value

    def make_empty(self):
        return self.make_response('')

    def make_redirect(self):
        if not self._redirect:
            raise Exception('Cannot create a redirect response without a redirect')
        if self.call:
            raise Exception('Cannot combine use make_response when a callable is set')
        return redirect(*self.redirect)

    def make_call(self):
        if self.modified:
            # If we receive a callabke - e.g. a lambda calling another RH - we do not allow any
            # external modifications
            raise Exception('Cannot combine callable with custom modifications or a return value')
        return self.call()

    def make_response(self, res):
        if self.call:
            raise Exception('Cannot combine use make_response when a callable is set')

        if isinstance(res, app.response_class):
            if self.modified:
                # If we receive a response - most likely one created by send_file - we do not allow any
                # external modifications.
                raise Exception('Cannot combine response object with custom modifications')
            return res

        if self._redirect:
            return self.make_redirect()

        res = app.make_response((res, self.status, self.headers))
        if self.content_type:
            res.content_type = self.content_type
        return res


class XAccelMiddleware(object):
    """A WSGI Middleware that converts X-Sendfile headers to X-Accel-Redirect
    headers if possible.

    If the path is not mapped to a URI usable for X-Sendfile we abort with an
    error since it likely means there is a misconfiguration.
    """

    def __init__(self, app, mapping):
        self.app = app
        self.mapping = mapping.items()

    def __call__(self, environ, start_response):
        def _start_response(status, headers, exc_info=None):
            xsf_path = None
            new_headers = []
            for name, value in headers:
                if name.lower() == 'x-sendfile':
                    xsf_path = value
                else:
                    new_headers.append((name, value))
            if xsf_path:
                uri = self.make_x_accel_header(xsf_path)
                if not uri:
                    raise ValueError('Could not map %s to an URI' % xsf_path)
                new_headers.append(('X-Accel-Redirect', uri))
            return start_response(status, new_headers, exc_info)

        return self.app(environ, _start_response)

    def make_x_accel_header(self, path):
        for base, uri in self.mapping:
            if path.startswith(base + '/'):
                return uri + path[len(base):]
