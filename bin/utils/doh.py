import getopt, sys

from MaKaC.common.db import DBMgr
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import DeletedObjectHolder, Conference, ConferenceHolder, Contribution, AcceptedContribution, SubContribution, CategoryManager
from base import prettyPrint
import time, datetime
from pytz import timezone

def findZombies(fix=False,fromDate=None):
    dbi = DBMgr.getInstance()
    dbi.startRequest()

    pubConfIdx = IndexesHolder().getIndex('OAIDeletedConferenceModificationDate')
    prvConfIdx = IndexesHolder().getIndex('OAIDeletedPrivateConferenceModificationDate')

    pubContIdx = IndexesHolder().getIndex('OAIDeletedContributionModificationDate')
    prvContIdx = IndexesHolder().getIndex('OAIDeletedPrivateContributionModificationDate')


    zombies = []
    doh = DeletedObjectHolder()

    for obj in doh.getList():
        isZombie = False
        rec = None

        if obj._objClass == Conference:
            try:
                rec = ConferenceHolder().getById(obj.getId())
                isZombie = True
            except:
                continue
        elif obj._objClass == Contribution or obj._objClass == AcceptedContribution:

            try:
                conference = ConferenceHolder().getById(obj.confId)
            except:
                continue

            rec = conference.getContributionById(obj.contribId)
            isZombie = (rec != None)
        elif obj._objClass == SubContribution:

            try:
                conference = ConferenceHolder().getById(obj.confId)
            except:
                continue

            contrib = conference.getContributionById(obj.contribId)
            if not contrib:
                continue
            rec = contrib.getSubContributionById(obj.subContribId)
            isZombie = (rec != None)

        if isZombie:
            print "-- ZOMBIE %s" % prettyPrint(rec)
            zombies.append(obj)


    if fix:
        for z in zombies:
            dbi.sync()

            pubConfIdx.unindexElement(z)
            prvConfIdx.unindexElement(z)
            pubContIdx.unindexElement(z)
            prvContIdx.unindexElement(z)

            id = z.getId()
            doh.remove(z)
            dbi.commit()
            print "-- FIXED %s " % id

    dbi.endRequest()
    print "\n Total of %s zombie records found" % len(zombies)

    return zombies


def findCamouflaged(fix=False,fromDate=None):

    table = {
        0: [Conference],
        1: [Contribution, AcceptedContribution],
        2: [SubContribution]
    }

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    camouflaged = []
    doh = DeletedObjectHolder()

    for obj in doh.getList():
        types = table[obj.getId().count(":")]
        if not obj._objClass in types:
            camouflaged.append(obj)
            print "-- CAMOUFLAGED %s (%s) should be in %s" % (prettyPrint(obj),
                                                           obj._objClass,
                                                           types)

    if fix:
        for c in camouflaged:
            dbi.sync()
            doh.remove(c)
            dbi.commit()
            print "-- FIXED %s " % prettyPrint(c)

    dbi.endRequest()
    print "\n Total of %s camouflaged conferences found" % len(camouflaged)

    return camouflaged

def reindex(fix=False,fromDate=None):

    """ Recreate deleted obj indices, from the DOH """

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    pubConfIdx = IndexesHolder().getIndex('OAIDeletedConferenceModificationDate')
    prvConfIdx = IndexesHolder().getIndex('OAIDeletedPrivateConferenceModificationDate')

    pubContIdx = IndexesHolder().getIndex('OAIDeletedContributionModificationDate')
    prvContIdx = IndexesHolder().getIndex('OAIDeletedPrivateContributionModificationDate')


    doh = DeletedObjectHolder()

    pubConfIdx.initIndex()
    pubContIdx.initIndex()
    prvConfIdx.initIndex()
    prvContIdx.initIndex()

    fromDateParsed_tz = datetime.datetime(*time.strptime(fromDate,'%Y-%m-%d')[:6],**{'tzinfo':timezone('UTC')})
    fromDateParsed_naive = datetime.datetime(*time.strptime(fromDate,'%Y-%m-%d')[:6])

    for obj in doh.getList():
        if fromDate:
            if obj.getOAIModificationDate().tzinfo:
                fromDateParsed = fromDateParsed_tz
            else:
                fromDateParsed = fromDateParsed_naive
            if obj.getOAIModificationDate() < fromDateParsed:
                continue
        if not hasattr(obj,'protected'):
            print "NO DATA FOR %s (%s)" % (obj.getId(), obj.getOAIModificationDate())
            continue
        print "indexing %s (%s)" % (prettyPrint(obj), obj.getOAIModificationDate())
        if obj._objClass == Conference:
            if obj.protected:
                prvConfIdx.indexConference(obj)
            else:
                pubConfIdx.indexConference(obj)
        elif obj._objClass == Contribution or obj._objClass == AcceptedContribution or obj._objClass == SubContribution:
            if obj.protected:
                prvContIdx.indexContribution(obj)
            else:
                pubContIdx.indexContribution(obj)
        dbi.commit()

    dbi.endRequest()


def guessProtection(fix=False,fromDate=None):

    """ Recreate deleted obj indices, from the DOH, guessing the protection,
    using the parent category"""

    dbi = DBMgr.getInstance()
    dbi.startRequest()

    doh = DeletedObjectHolder()

    if fromDate:
        fromDateParsed_tz = datetime.datetime(*time.strptime(fromDate,'%Y-%m-%d')[:6],**{'tzinfo':timezone('UTC')})
        fromDateParsed_naive = datetime.datetime(*time.strptime(fromDate,'%Y-%m-%d')[:6])

    for obj in doh.getList():
        if fromDate:
            if obj.getOAIModificationDate().tzinfo:
                fromDateParsed = fromDateParsed_tz
            else:
                fromDateParsed = fromDateParsed_naive
            if obj.getOAIModificationDate() < fromDateParsed:
                continue

        if not hasattr(obj, 'protected'):
            try:
                categ = CategoryManager().getById(obj.getCategoryPath()[-1])
                obj.protected = categ.hasAnyProtection()

                print "-- protection for %s set as %s" % (prettyPrint(obj), obj.protected)
            except KeyError:
                print ">> CATEGORY %s for %s no longer exists - assuming TRUE" % (obj.getCategoryPath()[-1], prettyPrint(obj))
                obj.protected = True

            dbi.commit()
        else:
            print "** protection for %s was already at %s" % (prettyPrint(obj), obj.protected)

    dbi.endRequest()



def process(options):

    dateFrom = None
    fix = False

    for o,v in options:
        if o == "--find-zombies":
            f,args = findZombies, []
        elif o == "--find-camouflaged":
            f, args = findCamouflaged, []
        elif o == "--reindex":
            f, args = reindex, []
        elif o == "--guess-protection":
            f, args = guessProtection, []
        elif o == "--from":
            dateFrom = v
        elif o == "--fix":
            fix = True

    args.extend([fix, dateFrom])
    f(*args)

if __name__ == '__main__':

    """ --find-zombies - Zombie events - they're dead and alive at the
        same time. That means they're in the DeletedObjectHolder, and
        linked to a specific category as well.
        --fix - Fixes the problem (for zombies, it assumes they're alive,
        and removes them from the DOH)
    """

    parsedOpt, rest = getopt.getopt(sys.argv[1:], '', ["find-zombies", "find-camouflaged", "fix", "reindex","guess-protection","from="])

    process(parsedOpt)

    if len(rest) > 0:
        print "Unrecognized: %s" % rest
        sys.exit(-1)
