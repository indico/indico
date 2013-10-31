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

import glob
import os
import sys
from optparse import OptionParser

from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph
# from sqlalchemy.orm import sessionmaker

from indico.core.db.schema import Base
# import every module under rb to init Base (preferred to __all__ in rb)
map(lambda m: __import__('indico.core.db.schema.rb.{0}'.format(m)),
    [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__) + "/*.py")])


def generate_schema_graph(db='test.db', output='test.png'):
    graph = create_schema_graph(metadata=MetaData('sqlite:///' + db),
                                show_datatypes=False,
                                show_indexes=False,
                                rankdir='LR', # or TP
                                concentrate=False) # no joins of tables together
    graph.write_png(output)

def generate_schema(db='test.db', checkfirst=False, echo=True):
    engine = create_engine('sqlite:///' + db, echo=echo)
    Base.metadata.create_all(engine, checkfirst=checkfirst)
    # Session = sessionmaker(bind=engine)
    # session = Session()
    print 'everything is fine for now!'

if __name__ == '__main__':
    args = sys.argv[1:]
    parser = OptionParser(usage="usage: %prog [-d db, -o ofile]")
    parser.add_option('-d', dest='db', help='db file path', metavar='FILE', default='test.db')
    parser.add_option('-o', dest='output', help='output file path', metavar='FILE', default='test.png')
    (options, args) = parser.parse_args()

    if args:
        parser.print_help()
    else:
        generate_schema(options.db);
        generate_schema_graph(options.db, options.output)
