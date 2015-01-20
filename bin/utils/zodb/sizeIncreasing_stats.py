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
from time import gmtime, strftime
from datetime import timedelta
from optparse import OptionParser
import cStringIO, cPickle
import optparse, getopt
import sys
import datetime
import os

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
    mb = kb / 1024.0
    if mb < 1024.0:
        return '%0.1fMb'%mb
    else:
        gb = mb/1024.0
        return '%0.1fGb'%gb

def run(path, days, notPacked):
    f = open(path, "rb")
    f.seek(0, 2)
    size= os.path.getsize(path)

    now = datetime.date.today()

    notPackedDays = []

    for day in range(notPacked):
	notPackedDays.append(str(now - timedelta(days=day+1)))

    #day->size
    stats = {}
    th = prev_txn(f)
    bool = True
    while bool:
        ts = TimeStamp(th.tid)
        then = datetime.date(int(ts.year()), int(ts.month()), int(ts.day()))
        delta = timedelta(days=int(days))

        if(now - then < delta):
            dateT = strftime("%Y-%m-%d", [int(ts.year()), int(ts.month()), int(ts.day()),1,1,1,1,1,1] )
            try:
                stats[dateT] = stats[dateT] + th.length
            except KeyError:
                stats[dateT] = th.length
        else:
            bool = False
        th = th.prev_txn()

    f.close()

    total = 0
    totalPacked = 0
    daysPacked = 0
    for (d,s) in sorted(stats.items(), key=lambda (k,v): v, reverse=True):
        print d,"size:", pretty_size(s),
        date = str(d)
        if(date in notPackedDays or date == str(now)):
            print "(not yet packed)"
        else:
            totalPacked = totalPacked + s
            daysPacked = daysPacked + 1
            print
        total = total + s


    if int(totalPacked):
        average = totalPacked/int(daysPacked)
    else:
        average = 0

    print "\n-- ALREADY PACKED DAYS--"
    print "The amount of data added in", daysPacked, "days is", pretty_size(totalPacked)
    print "Average", pretty_size(average), "per day"

    print "Following this trend, the size of the database will be:"
    print "\t",pretty_size(average*365+size)," in 1 year"
    print "\t",pretty_size(average*365*2+size)," in 2 years"
    print "\t",pretty_size(average*365*10+size)," in 10 years"

    print "\n-- ALL DAYS --"
    print "The amount of data added in", days, "days is", pretty_size(total)
    if int(total):
        print "Average", pretty_size(total/int(days)), "per day"
    else:
        print "Average 0bytes per day"



def main():
    usage = "usage: %prog [options] filename"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--days", dest="days", action="store",
                  help="show to amound of data added the last 'd' days")
    parser.add_option("-n", "--notPacked", dest="np", action="store", default = 2,
                  help="not packed days (starting from yesterday")

    (options, args) = parser.parse_args()

    days = 0

    if options.days:
        days = options.days
    else:
        print "You have to enter the number of days, see --help for details"
        return 2

    path = args[0]

    run(path, days, int(options.np))


if __name__ == "__main__":
    main()
