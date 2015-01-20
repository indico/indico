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

def run(path, tid):
    f = open(path, "rb")
    f.seek(0, 2)

    th = prev_txn(f)
    while (str(TimeStamp(th.tid)) != tid):
        th = th.prev_txn()

    reader = Reader()
    iterator = FileIterator(path, pos=th._pos)
    header = TxnHeader(f,th._pos)
    for i in iterator:
        if(str(TimeStamp(i.tid)) == tid):
            print "\nTRANSACTION: ", TimeStamp(i.tid), i.user, i.description, pretty_size(header.length),"\n"
            header = header.next_txn()
            object_types = {}
            for o in i:
                ot = reader.getIdentity(o.data)
                print " - ", ot, pretty_size(len(o.data))
                ob = cPickle.loads(o.data)
                # Not sure why some objects are stored as tuple (object, ())
                if type(ob) == tuple and len(ob) == 2:
                    ob = ob[0]
                if hasattr(ob, "__dict__"):
                    for i in ob.__dict__.items():
                        if str(i[0]) == "__doc__":
                            print "\t('__doc__',", i[1],")"
                        elif not callable(i[1]):
                            print "\t",i
                else:
                    print "can't extract:" + str(ob)
            break
    f.close()

def main():
    usage = "usage: %prog [options] filename"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--tid", dest="tid",
                  help="the researched transaction's tid", type="string")

    (options, args) = parser.parse_args()

    path = args[0]
    tid = options.tid

    run(path, tid)

if __name__ == "__main__":
    main()
