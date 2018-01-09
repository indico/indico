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

from __future__ import absolute_import, unicode_literals

import inspect
import os
import time
from importlib import import_module

from flask import send_file as _send_file
from flask import url_for as _url_for
from flask import Blueprint, current_app, g, redirect, request
from flask.helpers import get_root_path
from werkzeug.datastructures import FileStorage, Headers
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter, BuildError, UnicodeConverter
from werkzeug.wrappers import Response as WerkzeugResponse

from indico.util.caching import memoize
from indico.util.fs import secure_filename
from indico.util.locators import get_locator
from indico.web.util import jsonify_data


def discover_blueprints():
    """Discovers all blueprints inside the indico package

    Only blueprints in a ``blueprint.py`` module or inside a
    ``blueprints`` package are loaded. Any other files are not touched
    or even imported.

    :return: a ``blueprints, compat_blueprints`` tuple containing two
             sets of blueprints
    """
    package_root = get_root_path('indico')
    modules = set()
    for root, dirs, files in os.walk(package_root):
        for name in files:
            if not name.endswith('.py') or name.endswith('_test.py'):
                continue
            segments = ['indico'] + os.path.relpath(root, package_root).replace(os.sep, '.').split('.') + [name[:-3]]
            if segments[-1] == 'blueprint':
                modules.add('.'.join(segments))
            elif 'blueprints' in segments[:-1]:
                if segments[-1] == '__init__':
                    modules.add('.'.join(segments[:-1]))
                else:
                    modules.add('.'.join(segments))

    blueprints = set()
    compat_blueprints = set()
    for module_name in sorted(modules):
        module = import_module(module_name)
        for name in dir(module):
            obj = getattr(module, name)
            if name.startswith('__') or not isinstance(obj, Blueprint):
                continue
            if obj.name.startswith('compat_'):
                compat_blueprints.add(obj)
            else:
                blueprints.add(obj)
    return blueprints, compat_blueprints


def _convert_request_value(x):
    if isinstance(x, unicode):
        return x.encode('utf-8')
    elif isinstance(x, FileStorage):
        return x
    raise TypeError('Unexpected item in request data: %s' % type(x))


def create_flat_args():
    """Creates a dict containing the GET/POST arguments in a style old indico code expects.

    Do not use this for anything new - use request.* directly instead!"""
    args = request.args.copy()
    for key, values in request.form.iterlists():
        args.setlist(key, values)
    for key, values in request.files.iterlists():
        args.setlist(key, values)
    flat_args = {}
    for key, item in args.iterlists():
        flat_args[key] = map(_convert_request_value, item) if len(item) > 1 else _convert_request_value(item[0])
    return flat_args


@memoize
def make_view_func(obj):
    """Turns an object in to a view function.

    This function is called on each view_func passed to IndicoBlueprint.add_url_route().
    It handles RH classes and normal functions.
    """
    if inspect.isclass(obj):
        # Some class
        if hasattr(obj, 'process'):
            # Indico RH
            def wrapper(**kwargs):
                return obj().process()
        else:
            # Some class we didn't expect.
            raise ValueError('Unexpected view func class: %r' % obj)

        wrapper.__name__ = obj.__name__
        wrapper.__doc__ = obj.__doc__
        return wrapper
    elif callable(obj):
        # Normal function
        return obj
    else:
        # If you ever get this error you should probably feel bad. :)
        raise ValueError('Unexpected view func: %r' % obj)


@memoize
def redirect_view(endpoint, code=302):
    """Creates a view function that redirects to the given endpoint."""
    def _redirect(**kwargs):
        params = dict(request.args.to_dict(), **kwargs)
        return redirect(_url_for(endpoint, **params), code=code)

    return _redirect


def make_compat_redirect_func(blueprint, endpoint, view_func=None, view_args_conv=None):
    def _redirect(**view_args):
        # In case of POST we can't safely redirect since the method would switch to GET
        # and thus the request would most likely fail.
        if view_func and request.method == 'POST':
            return view_func(**view_args)
        # Ugly hack to get non-list arguments unless they are used multiple times.
        # This is necessary since passing a list for an URL path argument breaks things.
        view_args.update((k, v[0] if len(v) == 1 else v) for k, v in request.args.iterlists())
        if view_args_conv is not None:
            for oldkey, newkey in view_args_conv.iteritems():
                value = view_args.pop(oldkey, None)
                if newkey is not None:
                    view_args[newkey] = value
        try:
            target = _url_for('%s.%s' % (getattr(blueprint, 'name', blueprint), endpoint), **view_args)
        except (BuildError, ValueError):
            raise NotFound
        return redirect(target, 302 if current_app.debug else 301)
    return _redirect


def url_for(endpoint, *targets, **values):
    """Wrapper for Flask's url_for() function.

    The `target` argument allows you to pass some object having a `locator` property returning a dict.

    For details on Flask's url_for, please see its documentation.
    The important special arguments you can put in `values` are:

    _external: if set to `True`, an absolute URL is generated
    _scheme: a string specifying the desired URL scheme (only with _external) - use _secure if possible!
    _anchor: if provided this is added as #anchor to the URL.
    """

    if targets:
        locator = {}
        for target in targets:
            if target:  # don't fail on None or mako's Undefined
                locator.update(get_locator(target))
        intersection = set(locator.iterkeys()) & set(values.iterkeys())
        if intersection:
            raise ValueError('url_for kwargs collide with locator: %s' % ', '.join(intersection))
        values.update(locator)

    for key, value in values.iteritems():
        # Avoid =True and =False in the URL
        if isinstance(value, bool):
            values[key] = int(value)

    url = _url_for(endpoint, **values)
    if g.get('static_site') and not values.get('_external'):
        # for static sites we assume all relative urls need to be
        # mangled to a filename
        # we should really fine a better way to handle anything
        # related to offline site urls...
        from indico.modules.events.static.util import url_to_static_filename
        url = url_to_static_filename(endpoint, url)
    return url


def url_rule_to_js(endpoint):
    """Converts the rule(s) of an endpoint to a JavaScript object.

    Use this if you need to build an URL in JavaScript, but only if
    you really have to do that instead of e.g. building the URL on
    the server and storing it in a data attribute.

    JS usage::

        var urlTemplate = {{ url_rule_to_js('blueprint.endpoint') | tojson }};
        var url = build_url(urlTemplate[, params[, fragment]]);

    ``params`` is is an object containing the arguments and ``fragment``
    a string containing the ``#anchor`` if needed.
    """

    if endpoint[0] == '.':
        endpoint = request.blueprint + endpoint

    # based on werkzeug.contrib.jsrouting
    # we skip UnicodeConverter in the converters list since that one is the default and never needs custom js code
    return {
        'type': 'flask_rules',
        'endpoint': endpoint,
        'rules': [
            {
                'args': list(rule.arguments),
                'defaults': rule.defaults,
                'trace': [
                    {
                        'is_dynamic': is_dynamic,
                        'data': data
                    } for is_dynamic, data in rule._trace
                ],
                'converters': dict((key, type(converter).__name__)
                                   for key, converter in rule._converters.iteritems()
                                   if type(converter) is not UnicodeConverter)
            } for rule in current_app.url_map.iter_rules(endpoint)
        ]
    }


def redirect_or_jsonify(location, flash=True, **json_data):
    """Returns a redirect or json response.

    If the request was an XHR we return JSON, otherwise we redirect.
    Unless set to another value, the JSON data includes `success=True`

    :param location: the redirect target
    :param flash: if the json data should contain flashed messages
    :param json_data: the data to include in the json response
    """
    if request.is_xhr:
        return jsonify_data(flash=flash, **json_data)
    else:
        return redirect(location)


def _is_office_mimetype(mimetype):
    if mimetype.startswith('application/vnd.ms'):
        return True
    if mimetype.startswith('application/vnd.openxmlformats-officedocument'):
        return True
    if mimetype == 'application/msword':
        return True
    return False


def send_file(name, path_or_fd, mimetype, last_modified=None, no_cache=True, inline=None, conditional=False, safe=True):
    """Sends a file to the user.

    `name` is required and should be the filename visible to the user.
    `path_or_fd` is either the physical path to the file or a file-like object (e.g. a StringIO).
    `mimetype` SHOULD be a proper MIME type such as image/png. It may also be an indico-style file type such as JPG.
    `last_modified` may contain a unix timestamp or datetime object indicating the last modification of the file.
    `no_cache` can be set to False to disable no-cache headers.
    `inline` defaults to true except for certain filetypes like XML and CSV. It SHOULD be set to false only when you
    want to force the user's browser to download the file. Usually it is much nicer if e.g. a PDF file can be displayed
    inline so don't disable it unless really necessary.
    `conditional` is very useful when sending static files such as CSS/JS/images. It will allow the browser to retrieve
    the file only if it has been modified (based on mtime and size).
    `safe` adds some basic security features such a adding a content-security-policy and forcing inline=False for
    text/html mimetypes
    """

    name = secure_filename(name, 'file')
    assert '/' in mimetype
    if inline is None:
        inline = mimetype not in ('text/csv', 'text/xml', 'application/xml')
    if request.user_agent.platform == 'android':
        # Android is just full of fail when it comes to inline content-disposition...
        inline = False
    if _is_office_mimetype(mimetype):
        inline = False
    if safe and mimetype in ('text/html', 'image/svg+xml'):
        inline = False
    try:
        rv = _send_file(path_or_fd, mimetype=mimetype, as_attachment=not inline, attachment_filename=name,
                        conditional=conditional)
    except IOError:
        if not current_app.debug:
            raise
        raise NotFound('File not found: %s' % path_or_fd)
    if safe:
        rv.headers.add('Content-Security-Policy', "script-src 'self'; object-src 'self'")
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


# Note: When adding custom converters please do not forget to add them to converter_functions in routing.js
# if they need any custom processing (i.e. not just encodeURIComponent) in JavaScript.
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
    """

    def __init__(self):
        self.headers = Headers()
        self.status = 200
        self.content_type = None

    @property
    def modified(self):
        return bool(self.headers) or self.status != 200 or self.content_type

    def make_empty(self):
        return self.make_response('')

    def make_response(self, res):
        if isinstance(res, (current_app.response_class, WerkzeugResponse, tuple)):
            if self.modified:
                # If we receive a response - most likely one created by send_file - we do not allow any
                # external modifications.
                raise Exception('Cannot combine response object with custom modifications')
            return res

        # Return a plain string if that's all we have
        if not res and not self.modified:
            return ''

        res = current_app.make_response((res, self.status, self.headers))
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
        self.mapping = [(str(k), str(v)) for k, v in mapping.iteritems()]

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
                    raise ValueError('Could not map {} to a URI'.format(xsf_path))
                new_headers.append((b'X-Accel-Redirect', uri))
            return start_response(status, new_headers, exc_info)

        return self.app(environ, _start_response)

    def make_x_accel_header(self, path):
        for base, uri in self.mapping:
            if path.startswith(str(base + '/')):
                return uri + path[len(base):]
