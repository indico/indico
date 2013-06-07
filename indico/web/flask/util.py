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
import posixpath
import re
import time

from flask import request, redirect, url_for
from flask import current_app as app
from flask import send_file as _send_file
from werkzeug.datastructures import Headers, FileStorage
from werkzeug.exceptions import NotFound

from MaKaC.common import Config
from MaKaC.plugins.base import RHMapMemory
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


def create_flask_mp_wrapper(func):
    def wrapper():
        return func(None, **create_flat_args())

    return wrapper


def create_modpython_rules(app, folder, rule_folder='/'):
    for path in sorted(glob.iglob(os.path.join(app.root_path, folder, '*.py'))):
        name = os.path.basename(path)
        module_globals = {}
        execfile(path, module_globals)
        functions = filter(lambda x: callable(x[1]), module_globals.iteritems())
        base_url = posixpath.join(rule_folder, name)
        for func_name, func in functions:
            rule = base_url if func_name == 'index' else base_url + '/' + func_name
            endpoint = 'mp-%s-%s' % (re.sub(r'\.py$', '', name), func_name)
            app.add_url_rule(rule, endpoint, view_func=create_flask_mp_wrapper(func), methods=('GET', 'POST'))


@memoize
def create_flask_rh_wrapper(rh):
    def wrapper():
        return rh(None).process(create_flat_args())

    return wrapper


@memoize
def create_flask_rh_htdocs_wrapper(rh):
    def wrapper(filepath, plugin=None):
        path = rh.calculatePath(filepath, plugin=plugin)
        if not os.path.isfile(path):
            raise NotFound
        return _send_file(path)

    return wrapper


def create_plugin_rules(app):
    for rule, rh in RHMapMemory()._map.iteritems():
        endpoint = 'plugin-%s' % rh.__name__
        if issubclass(rh, RHHtdocs):
            app.add_url_rule(rule, endpoint, view_func=create_flask_rh_htdocs_wrapper(rh))
        else:
            app.add_url_rule(rule, endpoint, view_func=create_flask_rh_wrapper(rh), methods=('GET', 'POST'))


def shorturl_handler(what, tag):
    if what == 'categ':
        return redirect(url_for('mp-categoryDisplay-index', categId=tag))
    elif what == 'event':
        from MaKaC.webinterface.rh.conferenceDisplay import RHShortURLRedirect
        return RHShortURLRedirect(None).process({'tag': tag})


def send_file(name, path, ftype=None, last_modified=None, mimetype=None, no_cache=True, inline=False, conditional=False):
    # Note: path can also be a StringIO!
    as_attachment = request.user_agent.platform != 'android'  # is this still necessary?
    if inline:
        as_attachment = False
    if not bool(ftype) ^ bool(mimetype):
        raise ValueError('exactly one of mimetype and ftype are required')
    elif ftype:
        mimetype = Config.getInstance().getFileTypeMimeType(ftype)  # ftype is e.g. "JPG"
    rv = _send_file(path, mimetype=mimetype, as_attachment=as_attachment, attachment_filename=name,
                    conditional=conditional)
    if not as_attachment:
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
        return redirect(*self.redirect)

    def make_response(self, res):
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