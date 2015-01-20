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

"""Get statistics on objects stored.

Usage: objects_stats.py [-n number] tracefile
-n: display only the n biggest objects
-f: the FileStorage
"""

import datetime
import os
import struct
import time
import sys
import ZODB.MappingStorage
import ZODB.FileStorage
from ZODB import MappingStorage
from ZODB.utils import U64, get_pickle_metadata
from optparse import OptionParser
from ZODB.FileStorage.format \
     import TRANS_HDR, TRANS_HDR_LEN, DATA_HDR, DATA_HDR_LEN

from persistent.TimeStamp import TimeStamp
from datetime import timedelta

StringType = str

class Stat(object):
    def __init__(self):
        self.oid = None
        self.className = ""
        self.size = 0
        self.number = 0
        self.min = 0
        self.max = 0

def GetInHMS(seconds):
    hours = int(seconds / 3600)
    seconds -= 3600*hours
    minutes = int(seconds / 60.0)
    seconds -= 60.0*minutes
    if hours == 0:
        return "%02dmin" % (minutes)
    return "%02dh %02dmin" % (hours, minutes)

def pretty_size( size ):
    if size < 1024:
        return "%sB"%(size)
    kb = size / 1024.0
    if kb < 1024.0:
        return '%0.1fKb'%kb
    else:
        mb = kb/1024.0
        return '%0.1fMb'%mb

def U64(s):
    return struct.unpack(">Q", s)[0]

def oid_repr(oid):
    if isinstance(oid, StringType) and len(oid) == 8:
        return '%16x' % U64(oid)
    else:
        return repr(oid)

def main():
    usage = "usage: %prog [options] filename"
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--number", dest="num",
                  help="display only the n biggest objects", default=-1, type="int")
    parser.add_option("-f", "--output", dest="filename", action="store", type="string",
                  help="the FileStorage")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_false",
                  help="show percentage and time remaining")

    (options, args) = parser.parse_args()

    VERBOSE = False

    if options.filename:
        fname = options.filename
    else:
        print "You have to enter the FileStorage filename, see --help for details"
        return 2

    if options.verbose != None:
        VERBOSE = True

    objectsToDisplay = options.num
    stats = {}
    start = time.time()
    size = os.stat(fname).st_size

    it = ZODB.FileStorage.FileIterator(fname)

    lastPercent = 0.0
    recordsCounter = 0
    interval = 0.005
    now = datetime.date.today()

    try:

        for t in it:
            percent = float(it._file.tell())/float(size) * 100
            #Show the percentage of the work completed and the remaining time
            if(percent - lastPercent > interval):
                spentTime = time.time() - start
                remainingTime = spentTime / float(it._file.tell()) * (float(size)) - spentTime
                if VERBOSE:
                    sys.stderr.write("\r%f%% complete, time spent %s,  remaining time: %s, recordsCounter %d" % (percent,GetInHMS(time.time() - start),  GetInHMS(remainingTime), recordsCounter))
                sys.stdout.flush()
                lastPercent = percent

            for r in t:
                #need to reduce the time of the dictionary stats from time to time
                ts = TimeStamp(t.tid)
                then = datetime.date(int(ts.year()), int(ts.month()), int(ts.day()))
                delta = timedelta(days=3)

                #don't reduce the size of the dictionary when analysing last 3 days transactions
                if recordsCounter % (objectsToDisplay*100) == 0 and (now - then > delta):
                    tmp = {}
                    for class_name, s in sorted(
                        stats.items(), key=lambda (k,v): v.size, reverse=True)[0: objectsToDisplay]:
                        tmp[class_name] = s
                    stats = tmp

                if r.data:
                    mod, klass = get_pickle_metadata(r.data)
                    l = len(r.data)
                    class_name = mod + "." + klass + " oid: " +  oid_repr(r.oid).strip()
                    stat = stats.get(class_name)

                    if stat is None:
                        stat = stats[class_name] = Stat()
                        stat.size = stat.min = stat.max = l
                        stat.oid = oid_repr(r.oid).strip()
                        stat.className = mod + "." + klass
                        stat.number = 1
                    else:
                        stat.min = min(stat.min, l)
                        stat.max = max(stat.max, l)
                        stat.number = stat.number + 1
                        stat.size = stat.size + l

                    recordsCounter += 1

    except KeyboardInterrupt:
        pass

    print "\n"

    print "%-41s %9s %15s %15s %9s %9s %9s" % ("Module.ClassName", "Oid",  "Percentage", "Total Size", "Min", "Max", "Copies")
    print "%s" % "_" * 114

    for class_name, s in sorted(
        stats.items(), key=lambda (k,v): v.size, reverse=True)[0: objectsToDisplay]:

        class_name = s.className
        if len(class_name) > 40:
            class_name = class_name[::-1][0:35][::-1]
            class_name = "[..]" + class_name
        print "%-40s | %8s | %13f%% | %13s | %7s | %7s | %7s" % (class_name, s.oid, (s.size*100.0/size) , pretty_size(s.size), pretty_size(s.min), pretty_size(s.max), s.number)

if __name__ == '__main__':
    main()

