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

import glob
import os
import re
import time

from flask import request, redirect
from flask import current_app as app
from flask import send_file as _send_file
from werkzeug.datastructures import Headers

from MaKaC.common import Config


def _to_utf8(x):
    return x.encode('utf-8')


def create_flask_mp_wrapper(func):
    def wrapper():
        args = request.args.copy()
        args.update(request.form)
        flat_args = {}
        for key, item in args.iterlists():
            flat_args[key] = map(_to_utf8, item) if len(item) > 1 else _to_utf8(item[0])
        return func(None, **flat_args)
    return wrapper


def create_modpython_rules(app):
    for path in sorted(glob.iglob(os.path.join(app.root_path, 'htdocs/*.py'))):
        name = os.path.basename(path)
        module_globals = {}
        execfile(path, module_globals)
        functions = filter(lambda x: callable(x[1]), module_globals.iteritems())
        base_url = '/' + name
        for func_name, func in functions:
            rule = base_url if func_name == 'index' else base_url + '/' + func_name
            endpoint = 'mp-%s-%s' % (re.sub(r'\.py$', '', name), func_name)
            app.add_url_rule(rule, endpoint, view_func=create_flask_mp_wrapper(func), methods=('GET', 'POST'))


def send_file(name, path, ftype, last_modified=None, no_cache=True):
    as_attachment = request.user_agent.platform == 'android'  # is this still necessary?
    mimetype = Config.getInstance().getFileTypeMimeType(ftype)  # ftype is e.g. "JPG"
    rv = _send_file(path, mimetype=mimetype, as_attachment=as_attachment, attachment_filename=name)
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


class ResponseUtil(object):
    """This class allows "modifying" a Response object before it is actually created.

    The purpose of this is to allow e.g. an Indico RH to trigger a redirect but revoke
    it later in case of an error or to simply have something to pass around to functions
    which want to modify headers while there is no response available.
    """
    def __init__(self):
        self.headers = Headers()
        self._redirect = None
        self.status = 200
        self.content_type = None

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
        return redirect(*self.redirect)

    def make_response(self, res):
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