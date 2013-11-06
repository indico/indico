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

"""
Schema and graph generator
"""

import argparse

from sqlalchemy_schemadisplay import create_schema_graph

from indico.web.flask.app import make_app
from indico.core.db import db, load_room_booking


def generate_schema_graph(uri='sqlite:///test.db', output='test.png'):
    graph = create_schema_graph(metadata=db.MetaData(uri),
                                show_datatypes=False,
                                show_indexes=False,
                                rankdir='LR', # or TP
                                concentrate=False) # no joins of tables together
    graph.write_png(output)


def generate_schema(uri='sqlite:///test.db', checkfirst=True, echo=True):
    app = make_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    load_room_booking()
    db.init_app(app)
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('db', help='db file path')
    parser.add_argument('graph', help='graph output file path')
    args = parser.parse_args()

    generate_schema(args.db);
    generate_schema_graph(args.db, args.graph)
