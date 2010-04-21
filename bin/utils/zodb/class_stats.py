"""Get statistics on objects stored.

Usage: objects_stats.py [-n number] tracefile
-n: display only the n biggest classes
-f: the FileStorage
"""

import os
import struct
import time
import sys
import ZODB.MappingStorage
import ZODB.FileStorage
from ZODB.utils import U64, get_pickle_metadata
from optparse import OptionParser
from ZODB.FileStorage.format \
     import TRANS_HDR, TRANS_HDR_LEN, DATA_HDR, DATA_HDR_LEN

StringType = str

class Stat:
    n = 10

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
                  help="display only the n biggest classes", default=-1, type="int")
    parser.add_option("-f", "--file", dest="filename", action="store", type="string", 
                  help="your FileStorage")

    (options, args) = parser.parse_args()

    if options.filename:
        fname = options.filename
    else:
        print "You have to enter the filename, see --help for details"
        return 2

    objectsToDisplay = options.num
    stats = {}
    start = time.time()
    size = os.stat(fname).st_size

    it = ZODB.FileStorage.FileIterator(fname)

    lastPercent = 0.0
    recordsCounter = 0
    interval = 0.005

    try:
        for t in it:
            percent = float(it._file.tell())/float(size) * 100

            #Show the percentage of the work completed and the remaining time
            if(percent - lastPercent > interval):
                spentTime = time.time() - start
                remainingTime = spentTime / float(it._file.tell()) * (float(size)) - spentTime
                sys.stderr.write("\r%f%% complete, time spent %s,  remaining time: %s, recordsCounter %d" % (percent,GetInHMS(time.time() - start),  GetInHMS(remainingTime), recordsCounter))
           
                lastPercent = percent

            for r in t:
                #need to reduce the time of the dictionary stats from time to time
                if recordsCounter % (objectsToDisplay*100) == 0:  
                    tmp = {}       
                    for class_name, s in sorted(
                        stats.items(), key=lambda (k,v): v.total, reverse=True)[0: objectsToDisplay]:
                        tmp[class_name] = s
                    stats = tmp
                
                if r.data:
                    mod, klass = get_pickle_metadata(r.data)
                    l = len(r.data)
                    class_name = mod + "." + klass
                    stat = stats.get(class_name)
                    
		    if stat is None:
                        stat = stats[class_name] = Stat()
                        stat.min = stat.max = stat.total = l
                    else:
                        stat.min = min(stat.min, l)
                        stat.max = max(stat.max, l)
                        stat.total += l
                        stat.n += 1
                   
                    recordsCounter += 1

    except KeyboardInterrupt:
        pass

    print "\n"
    print "%-51s %15s %15s %15s %15s %15s" % ("Module.ClassName", "Percentage", "Min", "Max", "Size", "Instances")
    print "%s" % "_" * 134

    for class_name, s in sorted(
        stats.items(), key=lambda (k,v): v.total, reverse=True)[0: objectsToDisplay]:
        
        #Truncate the string if necessary        
        if len(class_name) > 50: 
            class_name = class_name[::-1][0:45][::-1]
            class_name = "[..]" + class_name
        print "%-50s | %15s%% | %13s | %13s | %13s | %13s" % (class_name, (s.total*100.0/size), pretty_size(s.min), pretty_size(s.max), pretty_size(s.total), s.n)
        

if __name__ == '__main__':
    main()

