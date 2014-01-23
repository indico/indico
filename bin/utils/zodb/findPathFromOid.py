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

import os
import time
import sys
from ZODB.utils import  p64, U64
from types import StringType
from ZODB.utils import get_pickle_metadata
from ZODB.serialize import referencesf
from ZODB.FileStorage import FileStorage
from optparse import OptionParser

SHORTEST = False
ROOT = False

def oid_repr(oid):
    if isinstance(oid, StringType) and len(oid) == 8:
        return '%16x' % U64(oid)
    else:
        return repr(oid)

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

def buildRefmap(fs):
    '''build a refmap from a filestorage. look in every record of every
       transaction. build a dict of oid -> list((referenced oids, mod.klass))
    '''
    refmap = {}
    fsi = fs.iterator()
    size = os.stat(fs.__name__).st_size
    start = time.time()
    lastPercent = 0.0
    interval = 0.005
    print "[1/3] Computing the Reference Map"
    for txn in fsi:
        percent = float(fsi._file.tell())/float(size) * 100

        if(percent - lastPercent > interval):
            spentTime = time.time() - start
            remainingTime = spentTime / float(fsi._file.tell()) * (float(size)) - spentTime
            sys.stdout.write("\r%f%% complete, time spent %s,  remaining time: %s" % (percent,GetInHMS(time.time() - start, True),  GetInHMS(remainingTime, False)))
            lastPercent = percent
        for rec in txn:
            if rec.data:
                mod, klass = get_pickle_metadata(rec.data)
            refs = referencesf(rec.data)
            refmap[rec.oid] = (refs, mod+"."+klass)
    print "\n",
    return refmap

def buildBackRefsMap(refmap):
    backRefMap = {}
    nbElements = len(refmap)
    start = time.time()
    lastPercent = 0.0
    recordsCounter = 0
    interval = 0.005

    print "[2/3] Computing the Back Reference Map"

    for oid, (refs, modKlass) in refmap.iteritems():
        percent = float(recordsCounter)/float(nbElements) * 100

        if(percent - lastPercent > interval):
            spentTime = time.time() - start
            remainingTime = spentTime / float(recordsCounter) * (float(nbElements)) - spentTime
            sys.stdout.write("\r%f%% complete, time spent %s,  remaining time: %s" % (percent,GetInHMS(time.time() - start, True),  GetInHMS(remainingTime, False)))
            lastPercent = percent

        recordsCounter = recordsCounter + 1

        try:
            backRefMap[oid_repr(oid).strip()]
        except:
            backRefMap[oid_repr(oid).strip()] = []
        for ref in refs:
            try:
                tmp = list(backRefMap[oid_repr(ref).strip()])
            except:
                tmp = []

            tmp.append((oid, modKlass))
            backRefMap[oid_repr(ref).strip()] = tmp
    return backRefMap

def getBackRefs(target, backRefMap):
    '''Return a list of oids in the refmap who reference target
    '''
    oidlist = backRefMap[oid_repr(target).strip()]

    return oidlist

def doSearch(target, refmap):
    '''we computer all the path from target to other objects. Only simple path
       are taken into account.
       The research is done using a Breadth-first search.
    '''

    backRefMap = buildBackRefsMap(refmap)
    obj= refmap[target]

    path = [(target, obj[1])]
    paths = []
    paths.append(path)
    pathResults = []
    alreadyDone = []

    print "\n[3/3] Computing the path..."

    while True:
        if(len(paths) != 0):
            target2 = paths.pop()
        else:
            break

        path = list(target2)
        target = target2.pop()
        brefs = getBackRefs(target[0], backRefMap)

        if not brefs:
            tmp = list(path)
            global ROOT
            if oid_repr(tmp[-1][0]).strip() == '0' or not ROOT:
                pathResults.append(tmp)
            if(len(paths) != 0):
                bool = True
                #shows only path from the root
                continue
            else:
                break

        (bref, modKlass) = brefs[0]
        if target[0] in alreadyDone:
            continue
        alreadyDone.append(target[0])

        if len(brefs) == 1:

            tmp = list(path)

            #we compute only simple path, not possible to go through an already
            #visited class
            bool = True
            for (el, mod2Klass2) in tmp:
                if(mod2Klass2 == modKlass):
                    bool = False
            if bool:
                path.append((bref, modKlass))
                tmp = list(path)
                paths.insert(0,(tmp))
            continue

        #all the possible path from this node
        for node in brefs:
            pathTmp = []
            pathTmp = list(path)

            bool = True
            for (el, mod2Klass2) in pathTmp:
                if(mod2Klass2 == node[1]):
                    bool = False
            if bool:
                pathTmp.append((node[0], node[1]))
                paths.insert(0,(pathTmp))

        path.append((bref, modKlass))


    return pathResults

def main():
    usage = "usage: %prog [options] filename"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--oid", dest="oid",type="string", action="store",
                  help="the oid of the object")
    parser.add_option("-f", "--file", dest="filename", action="store", type="string",
                  help="your FileStorage")
    parser.add_option("-r", "--root", dest="root", action="store_false",
                  help="if you want to display only paths to from the root")
    parser.add_option("-s", "--shortest", dest="short", action="store_false",
                  help="if you want to display only the shortest path")

    (options, args) = parser.parse_args()

    if options.filename:
        fname = options.filename
    else:
        print "You have to enter the filename, see --help for details"
        return 2

    if options.oid:
        oid = options.oid
    else:
        print "You have to enter the oid, see --help for details"
        return 2

    global ROOT
    if options.root != None:
        ROOT = True
    if options.short != None:
        global SHORTEST
        SHORTEST = True

    storage = FileStorage(fname)

    paths = doSearch(p64(long(oid, 16)), buildRefmap(storage))

    #If one only wants to see the shortest path
    if SHORTEST and len(paths):
        paths = [sorted(paths, key=lambda(a): len(a), reverse=True)[-1]]

    for path in sorted(paths, key=lambda(a): len(a), reverse=True):
        print "\n"
        for (oid, modKlass) in path[0:-1]:
            print "[0x"+(oid_repr(oid).strip())+ ":", modKlass +"]", "<-",

        if oid_repr(path[-1][0]).strip() == '0':
            print "[0x0 ROOT]"
        else:
            print "[0x"+(oid_repr(path[-1][0]).strip())+ ":", path[-1][1] + "]"

if __name__ == '__main__':
    main()
