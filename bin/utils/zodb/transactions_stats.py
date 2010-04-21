"""Count Transaction for each day.

Usage: objects_stats.py [-n number] tracefile
-m: mean time between transactions
-f: the FileStorage
-d: show the stats only for the date d (format dd-mm-yyyy)
"""

import os
import sys
import struct
import time
import ZODB.FileStorage
from ZODB.utils import U64, get_pickle_metadata
from persistent.TimeStamp import TimeStamp
from ZODB.tests.StorageTestBase import zodb_unpickle
from optparse import OptionParser
from time import gmtime, strftime


StringType = str

class Stat(object):
    def __init__(self):
        self.mean = []
        self.n = 1

def GetInHMS(seconds, showSec):
    hours = int(seconds / 3600)
    seconds -= 3600*hours
    minutes = int(seconds / 60.0)
    seconds -= 60.0*minutes
    if hours == 0:
        if(showSec): return "%02dmin %02dsecs" % (minutes, seconds)
        else: return "%02dmin" % (minutes)

    if(showSec): return "%02dh %02dmin %02dsecs" % (hours, minutes, seconds)
    else: return "%02dh %02dmin" % (hours, minutes)

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
                  help="display only the 'n' busiest days", default=-1, type="int")
    parser.add_option("-f", "--file", dest="filename", action="store", type="string", 
                  help="your FileStorage")
    parser.add_option("-d", "--date", dest="date", action="store", type="string", 
                  help="show the stats only for the date d (format dd-mm-yyyy)")

    (options, args) = parser.parse_args()
    objectsToDisplay = options.num
    
    if options.filename:
        fname = options.filename
    else:
        print "You have to enter the filename, see --help for details"
        return 2

    stats = {}
    start = time.time()
    size = os.stat(fname).st_size
    it = ZODB.FileStorage.FileIterator(fname)

    lastPercent = 0.0
    recordsCounter = 0
    interval = 0.005
    dataFound = False

    try:
        for t in it:

            #Format the date of the current transaction following dd-mm-yyyy   
            ts = TimeStamp(t.tid)
            dateT = strftime("%d-%m-%Y", [int(ts.year()), int(ts.month()), int(ts.day()),0,0,0,0,0,0] )
            percent = float(it._file.tell())/float(size) * 100
            
            #Check if we found the searched date
            if options.date: 
                if str(dateT) == str(options.date):
                    dataFound = True
                elif dataFound:
                    break

            #Show the percentage of the work completed and the remaining time    
            if(percent - lastPercent > interval):
                spentTime = time.time() - start
                remainingTime = spentTime / float(it._file.tell()) * (float(size)) - spentTime
                sys.stderr.write("\r%f%% complete, time spent %s,  remaining time: %s, recordsCounter %d" % (percent,GetInHMS(time.time() - start, True),  GetInHMS(remainingTime, False), recordsCounter))
           
                lastPercent = percent

            for r in t:
                #need to reduce the time of the dictionary stats from time to time
                if recordsCounter % (objectsToDisplay*100) == 0:  
                    tmp = {}       
                    for date, s in sorted(
                        stats.items(), key=lambda (k,v): v.n, reverse=True)[0: objectsToDisplay]:
                        tmp[date] = s
                    stats = tmp
        
                if r.data:
                    mod, klass = get_pickle_metadata(r.data)
                    l = len(r.data)
                    stat = stats.get(dateT)
                    if stat is None:
                        stat = stats[dateT] = Stat()
                        stat.n = 1
                    else:
                        stat.n += 1
                    recordsCounter += 1 

            stat = stats.get(dateT) 
            if stat is not None:
                stat.mean.append(TimeStamp(t.tid).timeTime())   

    except KeyboardInterrupt:
        pass

    print "\n"
    print "%-15s %15s %21s" % ("Date", "Transactions", "Average interval")
    print "%s" % "_" * 56
    
    if options.date:      
        for date, s in sorted(
            stats.items(), key=lambda (k,v): v.n, reverse=True):
            meanTime = 0
            for i in range(1,len(s.mean)):
                meanTime += s.mean[i] - s.mean[i-1]
            if str(date) == str(options.date):
                print "%-15s %15d %15f secs" % (date, (s.n), meanTime/s.n) 
    else:     
        for date, s in sorted(
            stats.items(), key=lambda (k,v): v.n, reverse=True)[0: objectsToDisplay]:
            meanTime = 0
            for i in range(1,len(s.mean)):
                meanTime += s.mean[i] - s.mean[i-1]

            print "%-15s %15d %15f secs" % (date, (s.n), meanTime/s.n)
     

if __name__ == '__main__':
    main()

