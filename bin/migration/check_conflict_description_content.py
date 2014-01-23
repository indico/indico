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
from MaKaC.conference import ConferenceHolder, AcceptedContribution
from time import sleep

LOG_FILENAME=""

logFile = []
def log(txt):
    logFile.append(txt)
    print txt


def main():
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
                    for cont in conf.getContributionList():
                        #if not isinstance(cont, AcceptedContribution):
                            if "content" in cont.getFields().keys():
                                if cont.getFields()["content"]:
                                    if cont.getFields()["content"] != cont.description:
                                        log("  contribution %s : content field no empty and diffrent from description"%cont.getId())
                                else:
                                    #cont.setField("content",cont.description)
                                    cont.getFields()["content"] = cont.description
                                    cont._p_changed = 1
                            else:
                                #cont.setField("content",cont.description)
                                cont.getFields()["content"] = cont.description
                                cont._p_changed = 1
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
    logFile.append("ERROR Confs: %s"%", ".join(cErrorList))
    f = file(LOG_FILENAME, "w")
    f.write("\n".join(logFile))
    f.close()
if __name__ == "__main__":
    if LOG_FILENAME == "":
        LOG_FILENAME = raw_input("\n\nPlease write a filename (absolute path) for logging: ")
    main()
