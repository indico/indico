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

import glob
import os
import re

from flask import request


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