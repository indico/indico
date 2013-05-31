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

from flask import request, current_app as app, redirect
from werkzeug.datastructures import Headers


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


class ResponseUtil(object):
    """This class allows an indico RH to modify the response object"""
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
