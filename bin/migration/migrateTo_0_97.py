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
from MaKaC.webinterface import displayMgr

LOG_FILENAME="c:/tmp/migrate.log"

def log(txt):
    f = file(LOG_FILENAME, "a")
    f.write("\n%s"%txt)
    f.close()
    print txt

def run4eachConfFast():
    DBMgr.getInstance().startRequest()
    ch = ConferenceHolder()
    for conf in ch.getList():
        moveLogoToDisplayMgr(conf)
    DBMgr.getInstance().endRequest()


def run4eachConfSlowly():
    DBMgr.getInstance().startRequest()
    ch = ConferenceHolder()
    ids = []
    print "Getting conference IDs..."
    for conf in ch.getList():
        ids.append(conf.getId())
    totalNumberConfs=len(ids)
    DBMgr.getInstance().endRequest()
    print "Updating conferences..."
    i = 0
    N_CONF=10
    cErrorList=[]
    while ids:
        if len(ids) >= N_CONF:
            lids = ids[:N_CONF]
            del ids[:N_CONF]
        else:
            lids = ids
            ids = None
        for j in range(10):
            conf=None
            try:
                DBMgr.getInstance().startRequest()
                for id in lids:
                    conf = ch.getById(id)
                    log("check for conference %s: %s/%s"%(conf.getId(),i,totalNumberConfs))
                    i += 1
                DBMgr.getInstance().endRequest()
                print "wait 0.5s..."
                sleep(0.5)
                break
            except Exception, e:
                cErrorList.append(conf)
                i-=N_CONF
                log("error %s, retry %d time(s)"%(e,int(10-j)))
                sleep(int(j))
                DBMgr.getInstance().abort()



def moveLogoToDisplayMgr(conf):
    log("changing logo for conf %s"%conf.getId())
    im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).getImagesManager()
    im._logo = conf._logo


def main():
    run4eachConfFast()

if __name__ == "__main__":
    if LOG_FILENAME == "":
        LOG_FILENAME = raw_input("\n\nPlease write a filename (absolute path) for logging: ")
    main()
