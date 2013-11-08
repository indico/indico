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

import argparse
import importlib
import os

try:
    from sqlalchemy_schemadisplay import create_schema_graph, create_uml_graph
    from sqlalchemy import MetaData
    from sqlalchemy.orm import class_mapper
except ImportError:
    print 'You should install sqlalchemy and sqlalchemy-schemadisplay to create graphs'
    import sys
    sys.exit(0)


def load_all_modules(pkg_name):
    directory = os.path.dirname(importlib.import_module(pkg_name).__file__)
    for f in os.listdir(directory):
        if f.endswith('.py'):
            yield importlib.import_module('.' + f[:-3], pkg_name)
        elif os.path.isdir(os.path.join(directory, f)):
            for m in load_all_modules(pkg_name + '.' + f):
                yield m


def generate_schema_graph(uri, output):
    graph = create_schema_graph(metadata=MetaData(uri),
                                show_datatypes=False,
                                show_indexes=False,
                                rankdir='LR', # or TP
                                concentrate=False) # no joins of tables together
    graph.write_png(output)


def generate_uml_graph(package, output):
    mappers = []
    for module in sorted(load_all_modules(package), key=lambda m: m.__name__):
        for attr in dir(module):
            if not attr.startswith('_'):
                try:
                    mappers.append(class_mapper(getattr(module, attr)))
                except Exception, e:
                    print str(e)

    graph = create_uml_graph(mappers, show_operations=False, show_multiplicity_one=False)
    graph.write_png(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    uml = parser.add_argument_group('UML')
    uml.add_argument('-p', '--package', help='database connection uri',
                     nargs='?')
    uml.add_argument('-u', '--uml_output', help='uml diagram output path',
                     nargs='?')

    schema = parser.add_argument_group('SCHEMA')
    schema.add_argument('-d', '--database', help='generate schema diagram',
                        nargs='?')
    schema.add_argument('-s', '--schema_output', help='schema graph output path',
                        nargs='?')

    args = parser.parse_args()

    if args.database and args.schema_output:
        generate_schema_graph(args.database, args.schema_output)
    elif not (not args.database and not args.schema_output):
        print '-d and -s must be supplied together'

    if args.package and args.uml_output:
        generate_uml_graph(args.package, args.uml_output)
    elif not(not args.package and not args.uml_output):
        print '-p and -u must be supplied together'
