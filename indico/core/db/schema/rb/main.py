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
import glob
import importlib
import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph
# from sqlalchemy.orm import sessionmaker

from indico.core.db.schema import Base, init_rb


def generate_schema_graph(db='test.db', output='test.png'):
    graph = create_schema_graph(metadata=MetaData('sqlite:///' + db),
                                show_datatypes=False,
                                show_indexes=False,
                                rankdir='LR', # or TP
                                concentrate=False) # no joins of tables together
    graph.write_png(output)

def generate_schema(db='test.db', checkfirst=True, echo=True):
    engine = create_engine('sqlite:///' + db, echo=echo)
    init_rb()
    Base.metadata.create_all(engine, checkfirst=checkfirst)
    # Session = sessionmaker(bind=engine)
    # session = Session()
    print 'everything is fine for now!'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('db', help='db file path')
    parser.add_argument('graph', help='graph output file path')
    args = parser.parse_args()

    generate_schema(args.db);
    generate_schema_graph(args.db, args.graph)
