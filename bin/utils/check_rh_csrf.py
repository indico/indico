# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import itertools
from importlib import import_module

import click
from flask import current_app
from terminaltables import AsciiTable

from indico.util.console import cformat
from indico.web.flask.app import make_app
from indico.web.flask.util import make_view_func


def get_all_subclasses(cls):
    all_subclasses = set()

    for subclass in cls.__subclasses__():
        all_subclasses.add(subclass)
        all_subclasses |= get_all_subclasses(subclass)

    return all_subclasses


def find_rhs(base, unsafe_only):
    reverse_view_funcs = {v: k for k, v in current_app.view_functions.iteritems()}
    table_data = []
    for cls in sorted({cls for cls in get_all_subclasses(base) if cls.CSRF_ENABLED is None}):
        try:
            endpoint = reverse_view_funcs[make_view_func(cls)]
        except KeyError:
            continue
        methods = set(itertools.chain.from_iterable(r.methods for r in current_app.url_map.iter_rules(endpoint)))
        safe = not bool(methods - {'GET', 'OPTIONS', 'HEAD'})
        if not safe or not unsafe_only:
            table_data.append([cformat('%{green!}SAFE%{reset}' if safe else '%{red!}DANGER%{reset}'),
                               cls.__module__, cls.__name__])
    if table_data:
        table_data.sort()
        headers = [['Status', 'Module', 'Class']]
        print AsciiTable(headers + table_data).table
    else:
        print cformat('%{green}No RHs without a CSRF_ENABLED value')


def _main(base, unsafe_only):
    segments = base.split('.')
    module = import_module('.'.join(segments[:-1]))
    base_cls = getattr(module, segments[-1])
    find_rhs(base_cls, unsafe_only)


@click.command()
@click.argument('base', default='indico.legacy.webinterface.rh.base.RH')
@click.option('--unsafe-only', is_flag=True, help='Skip safe classes')
def main(base, unsafe_only):
    """Show RH subclasses that do not have anything set for CSRF_ENABLED.

    Classes listed as SAFE do modify data and thus the CSRF setting
    does not matter (but it could be safely enabled).

    Classes listed as DANGER should have CSRF checks enabled and checked
    to ensure they work fine with CSRF checks enabled.
    """
    with make_app().app_context():
        _main(base, unsafe_only)


if __name__ == '__main__':
    main()
