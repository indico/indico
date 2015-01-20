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

from indico.core.db import DBMgr
from MaKaC.conference import ConferenceHolder
from MaKaC import conference
from MaKaC.trashCan import TrashCanManager
import MaKaC.common.indexes as indexes
from time import sleep

def date2txt(date):
    return date.strftime("%Y-%m-%d")

def main():
    DBMgr.getInstance().startRequest()
    ch = ConferenceHolder()
    ih = indexes.IndexesHolder()
    catIdx = ih.getById("category")
    confIdx = ih.getById("OAIConferenceModificationDate")
    contIdx = ih.getById("OAIContributionModificationDate")
    confIdxPr = ih.getById("OAIPrivateConferenceModificationDate")
    contIdxPr = ih.getById("OAIPrivateContributionModificationDate")
    confIdx.initIndex()
    contIdx.initIndex()
    confIdxPr.initIndex()
    contIdxPr.initIndex()
    DBMgr.getInstance().commit()
    print "Count conferences..."
    ids = catIdx.getItems('0')
    totalConf = len(ids)
    print "%d conferences found"%totalConf
    ic = 1
    DBMgr.getInstance().sync()
    DBMgr.getInstance().endRequest()
    i = 0
    pubConf = 0
    privConf = 0
    while ids:
        if len(ids) >= 10:
            lids = ids[:10]
            del ids[:10]
        else:
            lids = ids
            ids = None
        startic = ic
        startPubConf = pubConf
        startPrivConf = privConf
        for j in range(10):
            try:
                DBMgr.getInstance().startRequest()
                for id in lids:
                    conf = ch.getById(id)
                    confIdx = ih.getById("OAIConferenceModificationDate")
                    contIdx = ih.getById("OAIContributionModificationDate")
                    confIdxPr = ih.getById("OAIPrivateConferenceModificationDate")
                    contIdxPr = ih.getById("OAIPrivateContributionModificationDate")
                    print "Index conference %s: %d on %d"%(id, ic, totalConf)
                    ic += 1
                    if conf.hasAnyProtection():
                        confIdxPr.indexConference(conf)
                        privConf += 1
                    else:
                        confIdx.indexConference(conf)
                        pubConf += 1
                    for cont in conf.getContributionList():
                        if cont.hasAnyProtection():
                            contIdxPr.indexContribution(cont)
                        else:
                            contIdx.indexContribution(cont)
                        for sc in cont.getSubContributionList():
                            if cont.isProtected():
                                contIdxPr.indexContribution(sc)
                            else:
                                contIdx.indexContribution(sc)
                DBMgr.getInstance().endRequest()
                print "wait 0.5s..."
                sleep(0.5)
                break
            except Exception, e:
                print "error %s, retry %d time(s)"%(e,int(10-j))
                sleep(int(j))
                ic = startic
                pubConf = startPubConf
                privConf = startPrivConf
                DBMgr.getInstance().abort()
    print "indexed conferences : %d public, %d private"%(pubConf, privConf)

if __name__ == "__main__":
    main()

