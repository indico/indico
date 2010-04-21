##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
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

def run(path, ntxn, orderTransactions):
    f = open(path, "rb")
    f.seek(0, 2)

    th = prev_txn(f)
    for i in range(ntxn-1):
        th = th.prev_txn()

    reader = Reader()
    iterator = FileIterator(path, pos=th._pos)
    header = TxnHeader(f,th._pos)
    transactions = []
    for i in iterator:
        transactions.append({"tid": TimeStamp(i.tid), "user": i.user, "desc": i.description, "len": header.length, "objs": None})
        
        header = header.next_txn()   
    
        object_types = {}
        for o in i:
            ot = reader.getIdentity(o.data)
            if ot in object_types:
                size, count = object_types[ot]
                object_types[ot] = (size+len(o.data), count+1)
            else:
                object_types[ot] = (len(o.data),1)

        keys = object_types.keys()
        transactions[-1]["objs"] = object_types
            
    f.close()
    if orderTransactions:
        transactions = sorted(transactions, key=lambda (d): d["len"], reverse=True)
    for tr in transactions:
        print "\n\nTRANSACTION: ", tr["tid"], tr["user"], tr["desc"], pretty_size(tr["len"])
        object_types = tr["objs"]        
        keys = object_types.keys()        
        for k in sorted(keys, key=lambda (k): object_types[k][0], reverse=True):
            # count, class, size (aggregate)
            print " - ", object_types[k][1], k, pretty_size(object_types[k][0])

def main():
    usage = "usage: %prog [options] filename"
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--number", dest="num",
                  help="display the last 'n' transactions (Default 100)", default=100, type="int")
    parser.add_option("-o", "--order", dest="order", action="store_false", 
                  help="order the transactions by size and not by date")

    (options, args) = parser.parse_args()

    ntxn = options.num
    path = args[0]
    orderTransactions = False

    if options.order != None:
        orderTransactions = True

    run(path, ntxn, orderTransactions)


if __name__ == "__main__":
    main()
