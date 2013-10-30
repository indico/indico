import glob
import os
import sys
from optparse import OptionParser

from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph
# from sqlalchemy.orm import sessionmaker

from indico.core.db.schema import Base
map(lambda m: __import__('indico.core.db.schema.rb.{0}'.format(m)),
    [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__) + "/*.py")])


def generate_schema_graph(db='test.db', output='test.png'):
    graph = create_schema_graph(metadata=MetaData('sqlite:///' + db),
                                show_datatypes=False,
                                show_indexes=False,
                                rankdir='LR', # or TP
                                concentrate=False) # no joins of tables together
    graph.write_png(output)

def generate_schema(db, checkfirst=False):
    engine = create_engine('sqlite:///' + db, echo=True)
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
