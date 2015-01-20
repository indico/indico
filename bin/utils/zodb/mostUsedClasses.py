# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from ZODB.fstools import prev_txn, TxnHeader
from ZODB.serialize import ObjectReader, get_refs
from persistent.TimeStamp import TimeStamp
from ZODB.FileStorage.FileStorage import FileIterator
import cStringIO, cPickle
from optparse import OptionParser
import optparse, getopt
import sys
from datetime import timedelta
import datetime
from time import gmtime, strftime

class Nonce(object): pass

class Reader(ObjectReader):

    def __init__(self):
        self.identity = None

    def _get_unpickler(self, pickle):
        file = cStringIO.StringIO(pickle)
        unpickler = cPickle.Unpickler(file)
        unpickler.persistent_load = self._persistent_load

        def find_global(modulename, name):
            self.identity ="%s.%s"%(modulename, name)
            return Nonce

        unpickler.find_global = find_global

        return unpickler

    def getIdentity(self, pickle ):
        self.identity = None
        unpickler = self._get_unpickler( pickle )
        unpickler.load()
        return self.identity

    def getObject(self, pickle):
        unpickler = self._get_unpickler( pickle )
        ob = unpickler.load()
        return ob

def pretty_size( size ):
    if size < 1024:
        return "%sB"%(size)
    kb = size / 1024.0
    if kb < 1024.0:
        return '%0.1fKb'%kb
    else:
        mb = kb/1024.0
        return '%0.1fMb'%mb

def run(path, days, notPacked):
    f = open(path, "rb")
    f.seek(0, 2)
    now = datetime.date.today()

    #day->size
    stats = {}
    th = prev_txn(f)

    bool = True
    while bool:
        ts = TimeStamp(th.tid)
        then = datetime.date(int(ts.year()), int(ts.month()), int(ts.day()))
        delta = timedelta(days=int(days))
        if( not(now - then < delta)):
            bool = False
        th = th.prev_txn()

    reader = Reader()
    iterator = FileIterator(path, pos=th._pos)
    for i in iterator:
        object_types = {}
        for o in i:
            ot = reader.getIdentity(o.data)
            try:
                stats[ot] = stats[ot] + 1
            except KeyError:
                stats[ot] = 1
    f.close()

    for (o,n) in sorted(stats.items(), key=lambda (k,v): v, reverse=True):
        print "%6d: %s" % (n,o)


def main():
    usage = "usage: %prog [options] filename"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--days", dest="days", action="store",
                  help="show the most used classes during the last 'd' days")

    (options, args) = parser.parse_args()

    days = 0

    if options.days:
        days = options.days
    else:
        print "You have to enter the number of days, see --help for details"
        return 2

    path = args[0]

    run(path, days, int(options.days))


if __name__ == "__main__":
    main()
