import MaKaC
from MaKaC.common.db import DBMgr
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import DeletedObjectHolder
from MaKaC.conference import ConferenceHolder

import getopt, sys

from base import prettyPrint, getParent

def listIndex(idxName ,ids):
    DBMgr.getInstance().startRequest()
    idx = IndexesHolder().getIndex(idxName)

    for k,v in idx._words.iteritems():
        if ids:
            f = lambda x: str(x.getId())
        else:
            f = prettyPrint
        print k,map(f, v)

    DBMgr.getInstance().endRequest()

## def fixOrphans(idxName):
##     DBMgr.getInstance().startRequest()
##     idx = IndexesHolder().getIndex(idxName)

##     for k,l in idx._words.iteritems():
##         for v in l[:]:
##             if type(v) != MaKaC.conference.DeletedObject:
##                 parent = getParent(v)
##                 orphan = False

##                 if parent == None:
##                     print "[1st deg ORPHAN] %s" % prettyPrint(v)
##                     orphan = True
##                 elif hasattr(parent, 'getOwnerList') and parent.getOwnerList() == []:
##                     print "[2nd deg ORPHAN] %s %s" % (prettyPrint(v), parent)
##                     orphan = True

##                 if orphan:
##                     words = idx._words
##                     l = words[k]
##                     l.remove(v)
##                     words[k] = l
##                     idx.setIndex(words)

##                     ids = idx._ids
##                     l = words[k]
##                     l.remove(v.id)
##                     ids[k] = l

    DBMgr.getInstance().endRequest()

def searchForId(idxName, id):
    DBMgr.getInstance().startRequest()
    idx = IndexesHolder().getIndex(idxName)

    for k,l in idx._ids.iteritems():
        for v in l:
            if v == id:
                print "%s" % k
    DBMgr.getInstance().endRequest()


def countIndex(idxName):
    DBMgr.getInstance().startRequest()
    idx = IndexesHolder().getIndex(idxName)

    print len(sum(idx._words.values(), []))

    DBMgr.getInstance().endRequest()

def getEntry(idxName, entry, ids):
    DBMgr.getInstance().startRequest()
    idx = IndexesHolder().getIndex(idxName)

    if ids:
        if idx._ids.has_key(entry):
            print entry,idx._ids[entry]
        else:
            print "Key '%s' was not found" % entry
    else:
        if idx._words.has_key(entry):
            print entry, map(prettyPrint,idx._words[entry])
        else:
            print "Key '%s' was not found" % entry

    DBMgr.getInstance().endRequest()


class OAIModificationDate:

    def __init__(self, idx):
        self.idx = idx

    def checkOAIModificationTime(self, k, c):
        if k != c.getOAIModificationDate().strftime("%Y-%m-%d"):
            print "[ERR] Key '%s' does not match with mod. date %s (%s)!" % (k,c.getOAIModificationDate(),prettyPrint(c))
            self.err += 1

    def checkProtection(self, k, c):
        if not c.getOwner():
            print "[WARN] Since event '%s' is orphaned, protection cannot be checked" % prettyPrint(c)
        elif not self.isVisible(c):
            print  "[ERR] Conference '%s' should not be here (protection)" % prettyPrint(c)
            self.err += 1

    def checkLooseness(self, k, c, fix):
        orphan = False
        parent = getParent(c)
        if parent == None:
            print "[1st deg ORPHAN] %s\n" % prettyPrint(c)
            orphan = True
        elif hasattr(parent, 'getOwnerList') and parent.getOwnerList() == []:
            print "[2nd deg ORPHAN] %s %s\n" % (prettyPrint(c), parent)
            orphan = True

        if orphan and fix:

            DBMgr.getInstance().sync()

            print "Fixing %s..." % prettyPrint(c),
            if orphan:
                words = self.idx._words
                l = words[k]
                pos = l.index(c)
                print "del val %s\n" % l[pos]
                del l[pos]
                words[k] = l
                self.idx.setIndex(words)

                ids = self.idx._ids
                l = ids[k]
                print "del key %s\n" % l[pos]
                del l[pos]
                ids[k] = l

            DBMgr.getInstance().commit()

            print "Done!\n"



    def check(self, dfrom, fix, showProgress):
        print "Checking %s..." % self.name

        self.count = 0
        self.err = 0

        entryCount = 0

        keys = list(self.idx._words.keys())

        if dfrom:
            startPos = keys.index(dfrom)
        else:
            startPos = 0

        keys = keys[startPos:]

        totalLen = len(keys)

        for k in keys:

            l = self.idx._words[k]

            if showProgress:
                print >> sys.stderr, "%s/%s %s%%" % (entryCount, totalLen, (entryCount*100/totalLen)), '\r',

            for c in l:
                self.checkLooseness(k,c, fix)
                self.checkOAIModificationTime(k,c)
                self.checkProtection(k,c)
                self.count += 1

            entryCount += 1


        print "-- %s errors found in %s records" % (self.err,self.count)

    def inverseCheck(self):
        print "Searching through ConferenceHolder..."

        self.count = 0
        self.err = 0

        for c in ConferenceHolder().getList():
            k = c.getOAIModificationDate().strftime("%Y-%m-%d")
            if self.isVisible(c) and not self.idx._words.has_key(k):
                print "[ERR] Key '%s' not found (conf. %s - %s)!" % (k, c.getId(), c.getOAIModificationDate())
                self.err += 1
            else:
                if self.isVisible(c):
                    self.count += 1

                    if not c in self.idx._words[k]:
                        print "[ERR] Entry for conf. %s not found in %s [OAI modif. date: %s ]!" % (c.getId(), k, c.getOAIModificationDate())
                        self.err += 1

        print "-- %s errors found in %s records" % (self.err,self.count)


class OAIConferenceModificationDate(OAIModificationDate):
    name = 'OAIConferenceModificationDate'

    def isVisible(self, obj):
        return not obj.hasAnyProtection()

class OAIPrivateConferenceModificationDate(OAIModificationDate):
    name = 'OAIPrivateConferenceModificationDate'

    def isVisible(self, obj):
        return obj.hasAnyProtection()

class OAIContributionModificationDate(OAIModificationDate):
    name = 'OAIContributionModificationDate'

    def isVisible(self, obj):
        return not obj.hasAnyProtection()

class OAIPrivateContributionModificationDate(OAIContributionModificationDate):
    name = 'OAIPrivateContributionModificationDate'

    def isVisible(self, obj):
        return obj.hasAnyProtection()


def checkIndex(idxName, dfrom, fix, showProgress):

    DBMgr.getInstance().startRequest()

    idx = IndexesHolder().getIndex(idxName)

    if idxName == 'OAIConferenceModificationDate':
        OAIConferenceModificationDate(idx).check(dfrom, fix, showProgress)
    elif idxName == 'OAIPrivateConferenceModificationDate':
        OAIPrivateConferenceModificationDate(idx).check(dfrom, fix, showProgress)
    elif idxName == 'OAIContributionModificationDate':
        OAIContributionModificationDate(idx).check(dfrom, fix, showProgress)
    elif idxName == 'OAIPrivateContributionModificationDate':
        OAIPrivateContributionModificationDate(idx).check(dfrom, fix, showProgress)
    else:
        print "No checking procedures defined for %s" % idxName
        sys.exit(-1)
    DBMgr.getInstance().endRequest()

def inverseCheckIndex(idxName):
    DBMgr.getInstance().startRequest()

    idx = IndexesHolder().getIndex(idxName)

    if idxName == 'OAIConferenceModificationDate':
        OAIConferenceModificationDate(idx).inverseCheck()
    elif idxName == 'OAIPrivateConferenceModificationDate':
        OAIPrivateConferenceModificationDate(idx).inverseCheck()
    else:
        print "No inverse checking procedures defined for %s" % idxName
        sys.exit(-1)

    DBMgr.getInstance().endRequest()


def process(index, options):

    showProgress = True
    useIds = False
    fix = False
    dfrom = None

    for o,v in options:
        if o == '--ids':
            useIds = True
        elif o == '--list':
            f,args = listIndex, [index]
        elif o == '--count':
            countIndex(index)
        elif o == '--entry':
            f,args = getEntry, [index, v]
        elif o == '--check':
            f,args = checkIndex, [index]
        elif o == '--inverse-check':
            f,args = inverseCheckIndex, [index]
        elif o == '--fix':
            fix = True
        elif o == '--from':
            dfrom = v
        elif o == '--no-progress':
            showProgress = False
        elif o == '--search-id':
            f,args = searchForId, [index, v]

    if f == checkIndex:
        args.append(dfrom)
        args.append(fix)
        args.append(showProgress)

    if f in [listIndex, getEntry]:
        args.append(useIds)

    f(*args)


if __name__ == '__main__':
    parsedOpt, rest = getopt.getopt(sys.argv[2:], '', ["list","count","check","inverse-check","fix","search-id=","entry=","ids","from=","no-progress"])

    process(sys.argv[1], parsedOpt)

    if len(rest) > 0:
        print "Unrecognized: %s" % rest
        sys.exit(-1)
